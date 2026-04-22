from Git.ESD_P6.SDR_class import SDR
import numpy as np

SAMP_PER_BIT = 32  # ??? Skal minimum være 16 for at vi kan læse data
sample_rate = 1e6
center_freq = 5.8e9
gain = 60

sdr = SDR(sample_rate, center_freq, gain, gain, [1])

sdr.setup_receiving()


def center_normalize(sig):
    sig = sig - np.mean(sig)  # Remove DC
    sig_max = np.max(np.abs(sig))
    # NB ved sigmax = nul burde vi faktisk skippe resten af scriptet fordi der ikke er noget signal
    if sig_max == 0:
        return False
    sig = sig / sig_max  # Normalize to +- 1.0
    return sig


def frequency_correction(sig):
    # 2. Fine Carrier Frequency Offset (CFO) Correction (Squaring Method)
    # Required as the transmitter and receiver isnt syncronised on frequency.
    # Squaring BPSK removes the modulation, leaving a tone at 2x the CFO
    N_fft = 40000  # Zero-padded FFT for high frequency resolution
    sig_sq = sig ** 2
    fft_sq = np.fft.fft(sig_sq, n=N_fft)
    fft_sq[0] = 0  # Remove DC component
    freqs = np.fft.fftfreq(N_fft, d=1/sample_rate)

    # Search for the CFO peak within a reasonable +/- 50 kHz range
    valid_idx = np.where(np.abs(freqs) < 100000)[0]
    if len(valid_idx) == 0:
        return False

    peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
    cfo_est = freqs[peak_idx] / 2.0

    # Generate a complex exponential to completely "de-spin" the buffer
    t = np.arange(len(sig)) / sample_rate
    sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)
    return sig_cfo_corrected


def bit_extraction(sig, phase_offset, start_index, bits_to_extract):
    # 4. Final Phase Correction
    # Now that spinning is stopped, we fix the static phase offset
    # As the BPSK must be phase aligned to ensure correct decoding
    corrected_sig = sig * np.exp(-1j * phase_offset)
    real_sig = np.real(corrected_sig)

    # 5. Bit Extraction
    bits = []

    # Extract exactly 80 bits
    for i in range(bits_to_extract):
        idx = start_index + i * SAMP_PER_BIT
        bits.append('1' if real_sig[idx] > 0 else '0')

    return bits


def bit2ascii(bits):
    # 6. Decoding
    bit_str = "".join(bits)
    decoded_msg = ""

    # Step through 8 bits at a time
    for i in range(0, len(bit_str), 8):
        byte = bit_str[i:i+8]
        char_code = int(byte, 2)

        # Only keep printable ASCII
        if 32 <= char_code <= 126:
            decoded_msg += chr(char_code)

    return decoded_msg


def receive(sdr: SDR):
    # Pre-calculate Barker sequence parameters
    barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
    barker = np.repeat(barker_base, SAMP_PER_BIT)

    # Expected length of message
    EXPECTED_BITS = 80
    required_len = len(barker) + (EXPECTED_BITS * SAMP_PER_BIT)

    print("Listening...")
    sdr.start_receive_cont()
    buffer = np.zeros(10000, dtype=np.complex64)  # Premade buffer

    while True:

        sdr.receive_cont_samples(buffer)
        # print(buffer)

        # 1. DC Offset Removal & Normalization
        sig = center_normalize(buffer)
        if sig == False:
            continue  # Skip this loop

        sig_cfo_corrected = frequency_correction(sig)
        if sig_cfo_corrected == False:
            continue  # Skip this loop

        # 3. Frame Synchronization "Detecting" a preample
        corr = np.correlate(sig_cfo_corrected, barker, mode='valid')
        mag_corr = np.abs(corr)
        peak = np.argmax(mag_corr)

        # Threshold check: Max possible correlation is 416. We use 150 to reject noise.
        # Also ensure we have enough samples left in the buffer to pull all 80 bits.
        # NB hvis indført som en cirkulær buffer kunne dette være undgået
        if mag_corr[peak] > 150 and (peak + required_len < len(sig_cfo_corrected)):
            phase_offset = np.angle(corr[peak])

            # (Take sample at the middle of the signal, and not in the transistion region)
            start_index = peak + len(barker) + (SAMP_PER_BIT // 2)
            bits = bit_extraction(sig_cfo_corrected, phase_offset, start_index, EXPECTED_BITS)

            decoded_msg = bit2ascii(bits)

            print(decoded_msg)
            # if decoded_msg.strip():
            #    print(
            #        f"CFO Corrected: {cfo_est:5.0f} Hz | Static Phase: {np.degrees(phase_offset):6.1f}° | Decoded: {decoded_msg}")


if __name__ == "__main__":
    receive(sdr)
