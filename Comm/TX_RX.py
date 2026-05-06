from Git.ESD_P6.Comm.SPPEncoder import SPPEncoder
from Git.ESD_P6.SDR_class import SDR
import numpy as np
import time


class RXTX:
    def __init__(self, tx_apid, samples_pr_bit: int = 32, sample_rate: int | float = 1e6,
                 center_freq: int | float = 5.8e9, gain_rx: int = 60, gain_tx: int = 60,
                 down_sample_factor: int = 4):
        """
        samples_pr_bit:
           - Hvor mange samples er der på en bit? I.e. samplerate/samples_pr_bit = bit rate
        """
        self.samples_pr_bit = samples_pr_bit
        self.ds = down_sample_factor
        self.sample_rate_ds = sample_rate / down_sample_factor
        self.samples_pr_bit_ds = samples_pr_bit // down_sample_factor

        self.tx_apid = tx_apid
        self.sdr = SDR(sample_rate, center_freq, gain_rx, gain_tx, [0, 1])
        self.encode = SPPEncoder()
        self.last_state = ""
        self.barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
        self.new_buffer = np.zeros(20000, dtype=np.complex64)
        self.new_buffer_2D = np.zeros((2, 20000), dtype=np.complex64)

    def __center_normalize(self, sig):
        """Centers and normalizes the signal"""
        sig = sig - np.mean(sig)
        sig_max = np.max(np.abs(sig))
        if sig_max == 0:
            return False
        sig = sig / sig_max
        return sig

    def __frequency_correction(self, sig):
        """Corrects signal w.r.t. frequency offset using squaring method"""
        N_fft = 8192
        sig_sq = sig ** 2
        fft_sq = np.fft.fft(sig_sq, n=N_fft)
        freqs = np.fft.fftfreq(N_fft, d=1 / self.sample_rate_ds)

        valid_idx = np.where(np.abs(freqs) < 100000)[0]
        if len(valid_idx) == 0:
            return False

        peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
        cfo_est = freqs[peak_idx] / 2.0

        t = np.arange(len(sig)) / self.sample_rate_ds
        sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)
        return sig_cfo_corrected

    def __bit_extraction(self, sig, phase_offset, start_idx, bits_to_extract):
        """Extracts bits from signal given a known start index"""
        corrected_sig = sig * np.exp(-1j * phase_offset)
        indices = start_idx + np.arange(bits_to_extract) * self.samples_pr_bit_ds
        sample_values = np.real(corrected_sig[indices])
        bit_array = ['1' if v > 0 else '0' for v in sample_values]
        return bit_array

    def __bit2ascii(self, bits):
        """Converts bits (np array) to ASCII string"""
        rows = len(bits) // 8
        byte_matrix = bits[:rows * 8].reshape(-1, 8)
        powers = 2 ** np.arange(7, -1, -1)
        ascii_values = np.sum(byte_matrix * powers, axis=1)
        raw_bytes = bytes(ascii_values.astype(np.uint8))
        return raw_bytes.decode('ascii', errors='ignore')

    def recv_buffer(self, size: int):
        self.new_buffer = np.zeros(size, dtype=np.complex64)
        self.new_buffer_2D = np.zeros((2, size), dtype=np.complex64)

    def receive(self, length: int = 256, timeout: float = 5.0):
        """
        Receive a message, listening for up to `timeout` seconds.
        """
        if self.last_state != 'RX':
            self.sdr.setup_receiving()
            # FIX: small settle delay to let the UHD stream stabilise
            # before reading. Avoids consuming overrun/garbage buffers.
            time.sleep(0.05)
            self.last_state = 'RX'

        barker = np.repeat(self.barker_base, self.samples_pr_bit_ds)
        required_len = len(barker) + (length * self.samples_pr_bit_ds)

        wrap_over = []
        deadline = time.monotonic() + timeout
        rtn = []
        self.sdr.start_receive_cont()

        while time.monotonic() < deadline:
            self.sdr.receive_cont_samples(self.new_buffer_2D)
            self.new_buffer = self.new_buffer_2D[0]
            new_buffer_ds = self.new_buffer[::self.ds]

            buffer = np.concatenate((wrap_over, new_buffer_ds))
            wrap_over = buffer[-required_len:]  # carry tail into next iteration

            sig = self.__center_normalize(buffer)
            if isinstance(sig, bool):
                continue

            sig_cfo_corrected = self.__frequency_correction(sig)
            if isinstance(sig_cfo_corrected, bool):
                continue

            corr = np.correlate(sig_cfo_corrected, barker)
            mag_corr = np.abs(corr)

            noise_floor = np.median(mag_corr)
            peak_val = np.max(mag_corr)

            if peak_val > 2 * noise_floor and peak_val > (len(barker) * 0.5):
                indices = np.where(mag_corr > 0.9 * peak_val)[0]
            else:
                indices = []

            if len(indices) == 0:
                continue

            diffs = np.diff(indices)
            is_new_packet = diffs > len(barker)
            new_packet_starts = indices[1:][is_new_packet]
            starts = np.concatenate(([indices[0]], new_packet_starts))

            for start_idx in starts:
                window_end = min(start_idx + len(barker), len(mag_corr))
                peak = start_idx + np.argmax(mag_corr[start_idx:window_end])

                if peak + required_len < len(sig_cfo_corrected):
                    phase_offset = np.angle(corr[peak])
                    start_bit_idx = peak + len(barker) + (self.samples_pr_bit_ds // 2)
                    bits = self.__bit_extraction(sig_cfo_corrected, phase_offset,
                                                 start_bit_idx, length)
                    rtn.append(bits)

            if rtn != []:
                self.sdr.stop_receive_cont()
                self.new_buffer.fill(0)
                return rtn

        # Timed out without finding a packet
        self.sdr.stop_receive_cont()
        return None

    def transmit(self, msg: str, repeat: int = 5):
        """
        Transmit a message.
        """
        if self.last_state != 'TX':
            self.sdr.setup_transmit()
            time.sleep(0.05)   # let the TX stream settle before first send
            self.last_state = 'TX'

        packet = self.encode.encode(
            packet_type=0,
            apid=self.tx_apid,
            seq_flag=3,
            sequence_count=0,
            data=msg,
            sec_hdr_flag=0
        )

        data_symbols = np.array([1 if b == '1' else -1 for b in packet], dtype=np.float32)

        # CFO preamble tone (800 samples → 200 after DS=4, enough for 8192-pt FFT)
        t = np.arange(800) / self.samples_pr_bit
        cfo_preamble = np.exp(1j * 2 * np.pi * 0.1 * t).astype(np.complex64)

        payload = np.concatenate((self.barker_base, data_symbols)).astype(np.float32)
        data_samples = np.repeat(payload, self.samples_pr_bit).astype(np.complex64)

        # Gap between repetitions: enough silence so the receiver's barker
        # correlator sees a clean separation between packets.
        inter_packet_silence = np.zeros(self.samples_pr_bit * 200, dtype=np.complex64)
        lead_silence = np.zeros(self.samples_pr_bit * 50, dtype=np.complex64)
        tail_silence = np.zeros(self.samples_pr_bit * 50, dtype=np.complex64)

        # Build a single waveform with `repeat` packet bursts
        burst = np.concatenate((cfo_preamble, data_samples))
        repeated = np.concatenate(
            [lead_silence] +
            [np.concatenate((burst, inter_packet_silence)) for _ in range(repeat)] +
            [tail_silence]
        )

        self.sdr.transmit(repeated)

    def transmit_pure_sine(self, amount_samples: int):
        if self.last_state != 'TX':
            self.sdr.setup_transmit()
            self.last_state = 'TX'

        samples = np.ones(amount_samples, dtype=np.complex64)
        self.sdr.transmit(samples)

    def sample_and_rtn(self, samples: int):
        if self.last_state != 'RX':
            self.sdr.setup_receiving()
            self.last_state = 'RX'
        return (self.sdr.receive_num(samples))


# Example usage:
if __name__ == "__main__":
    s = RXTX()

    RX = True

    if RX:
        while True:
            result = s.receive(timeout=10.0)
            if result is not None:
                for item in result:
                    print(item)
    else:
        i = 0
        while True:
            i += 1
            s.transmit(str(i))
