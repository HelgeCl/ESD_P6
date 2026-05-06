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
        """Centers and normalizes the signal
        i.e. normalize (sig-mean(sig))
        """
        sig = sig - np.mean(sig)  # Remove DC
        sig_max = np.max(np.abs(sig))
        if sig_max == 0:  # If there is no signal, skip this cycle
            return False
        sig = sig / sig_max  # Normalize to +- 1.0
        return sig

    def __frequency_correction(self, sig):
        """
        Correting a signal w.r.t. frequency offset
        """
        # Carrier Frequency Offset (CFO) Correction
        # Required as the transmitter and receiver isnt syncronised on frequency.
        N_fft = 8192  # Size of FFT
        # Squaring BPSK removes the modulation, leaving a tone at 2x the CFO (See report)
        sig_sq = sig ** 2
        fft_sq = np.fft.fft(sig_sq, n=N_fft)

        # Get frequencies bins who's corresponding magnitude is fft_sq
        freqs = np.fft.fftfreq(N_fft, d=1/self.sample_rate_ds)

        # Search for the CFO peak within +- 50 kHz range (+- 100kHz as we square the signal)
        valid_idx = np.where(np.abs(freqs) < 100000)[0]
        if len(valid_idx) == 0:  # If no frequencies exist (in case of misconfiguration), this just returns before program throws errors
            return False

        # Find the index which corresponds to the maximum signal
        peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
        # estimate cfo as this maximum signal (remember to divide the freq by 2, to undo the squaring)
        cfo_est = freqs[peak_idx] / 2.0

        # Correct signal
        t = np.arange(len(sig)) / self.sample_rate_ds
        sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)  # e^(-j2pi f t)
        return sig_cfo_corrected

    def __bit_extraction(self, sig, phase_offset, start_idx, bits_to_extract):
        """Extects bits from signal
        Knowing the start index of the bits
        """
        corrected_sig = sig * np.exp(-1j * phase_offset)  # Correcting the signals phase offset
        # Corrected sig, is now frequency and phase corrected. Meaning that only real signal is left being between -1 and 1.
        # With bit 1 if signal is larger than 0 and 0 if smaller than 0.

        # Calculate the indices of all the bits (As start index is already centered, that is disregarded here)
        indices = start_idx + np.arange(bits_to_extract) * self.samples_pr_bit_ds
        # arange makes an array of 0 to arg. In this case 0 to length of packet

        # As indice has the index of every bit, we can just extact the signal at this index.
        # And as the signal is phase corrected we can just extract the real value
        sample_values = np.real(corrected_sig[indices])

        # Convert to '1's and '0's
        bit_array = (sample_values > 0).astype(np.uint8)  # If true 1, false = 0
        return bit_array

    def recv_buffer(self, size: int):
        """Change recv buffer size"""
        self.new_buffer = np.zeros(size, dtype=np.complex64)
        self.new_buffer_2D = np.zeros((2, size), dtype=np.complex64)

    def receive(self, length: int = 256, timeout: float = 5.0):
        """
        Receive a message, listening for up to `timeout` seconds.
        if length is larger than 20000 bits, call recv_buffer before with an appropiate size
        """
        if self.last_state != 'RX':
            self.sdr.setup_receiving()
            self.last_state = 'RX'

        # Calculate barker code:
        barker = np.repeat(self.barker_base, self.samples_pr_bit_ds)

        # Package length
        required_len = len(barker) + (length * self.samples_pr_bit_ds)

        wrap_over = [] # initialize for later use
        deadline = time.monotonic() + timeout #Implement a deadline time
        #NB monotonic clock is used instead of time.time() as this doesnt depend on system time
        #Which means it only goes forward, however if using time() and a system clock update happend
        #e..g 5 minutes backwards, the deadline would last an additional 5 minuts
        self.sdr.start_receive_cont()



        while time.monotonic() < deadline:
            self.sdr.receive_cont_samples(self.new_buffer_2D)
            self.new_buffer = self.new_buffer_2D[0] #SDR forces us to pull a 2D buffer
            #However we only need a 1D buffer
            new_buffer_ds = self.new_buffer[::self.ds]# Downsample the received buffer

            buffer = np.concatenate((wrap_over, new_buffer_ds)) #Insert wrap over
            wrap_over = buffer[-required_len:]  # Use the last part of the buffer for wrapover

            sig = self.__center_normalize(buffer)
            if isinstance(sig, bool):
                continue #loop skip (unusable data)

            sig_cfo_corrected = self.__frequency_correction(sig)
            if isinstance(sig_cfo_corrected, bool):
                continue #loop skip (unusable data)

            # Correlate the signal with the barker code
            corr = np.correlate(sig_cfo_corrected, barker)
            mag_corr = np.abs(corr)  # Magnitude of the complex numbers for comparason

            noise_floor = np.median(mag_corr)
            peak_corr = np.max(mag_corr)

            # len(barker) is the theortical maximum correlation (due to normalization)
            if peak_corr > 2 * noise_floor and peak_corr > (len(barker) * 0.75):
                indices = np.where(mag_corr > 0.9 * peak_corr)[0]
            else:
                indices = []

            # Indices is all index's which correlates well with the barker series
            if len(indices) == 0:
                continue #If no indices skip this loop
            
            #When at this point, we know that data has been found and we should return
            #Therefore we stop receiving samples
            self.sdr.stop_receive_cont()
            self.new_buffer.fill(0) #Dont really know why, but if we do not reset buffer
            # Issues arrise
            rtn = []

            # Detect only ONE start for every packet
            # Indices will have a lump of data, then a gap, then a new lump of data.
            # This is due to the barker seires being well correlated for a few samples, then a message, then a new barker comes
            # While also is well correlated

            # The goal is therefore to group these lumps together

            # Find gaps between indices to separate different potential packets
            # Calculates the difference between two successive elements
            diffs = np.diff(indices)
            # i.e. diff[1,2,10,5] = [2-1, 10-2, 5-10] = [1, 8, -5]
            # I.e. Output then shows, how many big the gap between indices is:
            # E.g. barker 1 results in indices 5,6,7,8,9,10
            # Barker 2 is 20,21,22,23,24,25
            # results in : 1,1,1,1,1,10,1,1,1,1

            # The goal is now to find indices, where the spacing/gap is larger than the length of the barker
            is_new_packet = diffs > len(barker)

            # Is_new_packet now cotains an array, with the same length as indices, but with "true and false" (0,1) values.
            # With "True", at the first indice for a new packet
            # Converting this to indices:
            # (Remember diff causes a skip of one element. Therefore we skip the first indices with indices[1:])
            new_packet_starts = indices[1:][is_new_packet]
            # new_packet_starts now contains the indices which corresponds to a new packet start
            # However it is missing the first element (due to the diff skipping the first element)
            # This first element is 100% sure a start of a packet, and should therefore be included
            # (We are sure of this, as it is the first time the barker correlates)
            starts = np.concatenate(([indices[0]], new_packet_starts))

            for start_idx in starts:
                # Make a window, from start index with the length of barker
                # with safety limit to not read outside mag_corr. NB if mag_corr is used, the next if statement will fail
                # And we'll get the packet next sample
                window_end = min(start_idx + len(barker), len(mag_corr))

                # Detect the peak index within this window
                peak = start_idx + np.argmax(mag_corr[start_idx:window_end])

                # Ensure that the entire packet is inside the signal
                if peak + required_len < len(sig_cfo_corrected):
                    # Calculate offset based on known the first value of barker is a 1
                    phase_offset = np.angle(corr[peak])
                    # Calculate index for first bit in the actual packet
                    start_bit_idx = peak + len(barker) + (self.samples_pr_bit_ds // 2)
                    # NB this index is places in the center of the samples. This ensures we are measuring in the stable region and not the transision

                    bits = self.__bit_extraction(sig_cfo_corrected, phase_offset,
                                                    start_bit_idx, length)
                    rtn.append(bits)  
                    return(rtn)              
            if rtn != []: #Sanity check
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
            self.last_state = 'TX'

        packet = self.encode.encode(
            packet_type=0,
            apid=self.tx_apid,
            seq_flag=3,
            sequence_count=0,
            data=msg,
            sec_hdr_flag=0
        )

        data_symbols = np.array([1 if bit == '1' else -1 for bit in packet], dtype=np.float32)
        carrier = np.ones(self.samples_pr_bit*20, dtype=np.float32)  # 20 bits of just carrier
        # required to get enough energy for FFT CFO

        payload = np.concatenate((self.barker_base, data_symbols)).astype(np.float32)
        data_samples = np.repeat(payload, self.samples_pr_bit).astype(np.complex64)
        
        #Building the repeated samples to be transmitted
        gap = np.zeros(self.samples_pr_bit*100, dtype=np.float32)
        #Gab required to space apart our repeats. Else we run the risk of a multipath causing interference
        burst = np.concatenate((gap, data_samples, carrier))
        repeated = np.concatenate([burst for _ in range(repeat)]).astype(np.complex64)

        self.sdr.transmit(repeated)

    def transmit_pure_sine(self, amount_samples: int):
        """Transmits a pure sine for "amount_samples". Done with the carrier set for this python object"""
        if self.last_state != 'TX':
            self.sdr.setup_transmit()
            self.last_state = 'TX'

        samples = np.ones(amount_samples, dtype=np.complex64)
        self.sdr.transmit(samples)

    def sample_and_rtn(self, samples: int):
        """returns a specific number of samples"""
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
