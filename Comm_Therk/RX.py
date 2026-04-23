import uhd
import numpy as np
from Git.ESD_P6.Comm_Therk.SPPDecoder import SPPDecoder

SAMP_PER_BIT = 32
sample_rate = 1e6    # 1 MHz (Lower is more stable for testing)
center_freq = 5.8e9  # 
tone_freq = 10e3     # 10 kHz (The frequency of the actual beep/tone)
gain = 40            # High gain for B200 antennas
rx_gain = 60
channels = [1]

# --- USRP Setup ---
usrp = uhd.usrp.MultiUSRP()
decoder = SPPDecoder(bit_rate=sample_rate)

for chan in channels:
    usrp.set_rx_antenna('TX/RX', chan)
    usrp.set_rx_gain(rx_gain, chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

    #usrp.set_tx_gain(gain, chan)
    usrp.set_tx_rate(sample_rate, chan)
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)


def receive():
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = channels
    rx_streamer = usrp.get_rx_stream(st_args)
    
    buffer = np.zeros(10000, dtype=np.complex64)
    metadata = uhd.types.RXMetadata()

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    rx_streamer.issue_stream_cmd(stream_cmd)

    # Pre-calculate Barker sequence parameters
    barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
    barker = np.repeat(barker_base, SAMP_PER_BIT)
    
    ### Data længde efter preamble
    EXPECTED_BITS = 256 # Tillader et 26 oktet datafelt (32 ialt)
    required_len = len(barker) + (EXPECTED_BITS * SAMP_PER_BIT)

    print("Listening...")
    while True:
        rx_streamer.recv(buffer, metadata)
        
        # 1. DC Offset Removal & Normalization
        sig = buffer - np.mean(buffer)
        sig_max = np.max(np.abs(sig))
        if sig_max == 0:
            continue
        sig = sig / sig_max # Normalize to +/- 1.0 for predictable thresholding
        
        # 2. Fine Carrier Frequency Offset (CFO) Correction (Squaring Method)
        # Squaring BPSK removes the modulation, leaving a tone at 2x the CFO
        N_fft = 40000  # Zero-padded FFT for high frequency resolution
        sig_sq = sig ** 2
        fft_sq = np.fft.fft(sig_sq, n=N_fft)
        fft_sq[0] = 0  # Remove DC component
        freqs = np.fft.fftfreq(N_fft, d=1/sample_rate)

        # Search for the CFO peak within a reasonable +/- 50 kHz range (Tone is 100 kHz)
        valid_idx = np.where(np.abs(freqs) < 100000)[0]
        if len(valid_idx) == 0:
            continue
            
        peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
        cfo_est = freqs[peak_idx] / 2.0

        # Generate a complex exponential to completely "de-spin" the buffer
        t = np.arange(len(sig)) / sample_rate
        sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)

        # 3. Frame Synchronization
        corr = np.correlate(sig_cfo_corrected, barker, mode='valid')
        mag_corr = np.abs(corr)
        peak = np.argmax(mag_corr)

        # Threshold check: Max possible correlation is 416. We use 150 to reject noise.
        # Also ensure we have enough samples left in the buffer to pull all 80 bits.
        if mag_corr[peak] > 150 and (peak + required_len < len(sig_cfo_corrected)):
            
            # 4. Final Phase Correction
            # Now that spinning is stopped, we fix the static phase offset
            phase_offset = np.angle(corr[peak])
            corrected_sig = sig_cfo_corrected * np.exp(-1j * phase_offset)
            real_sig = np.real(corrected_sig)

            # 5. Bit Extraction
            start_index = peak + len(barker) + (SAMP_PER_BIT // 2)
            bits = []
            
            # Extract exactly 80 bits
            for i in range(EXPECTED_BITS):
                idx = start_index + i * SAMP_PER_BIT
                bits.append('1' if real_sig[idx] > 0 else '0')
            
            # 6. Decoding
            decoded_packet = decoder.decode(bits)  # We can also pass bits to our SPPDecoder for structured parsing
            print(f"Received packet: {decoded_packet}")
            print(f"CFO Corrected: {cfo_est:5.0f} Hz | Static Phase: {np.degrees(phase_offset):6.1f}°")

if __name__ == "__main__":
    receive()