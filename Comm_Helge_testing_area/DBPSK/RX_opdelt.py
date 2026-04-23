from Git.ESD_P6.SDR_class import SDR
import numpy as np


SAMP_PER_BIT = 32  # Hvor mange samples er der på en bit? I.e. samplerate/SAMP_per_bit = bit rate
sample_rate = 1e6
center_freq = 5.8e9
gain = 60
DS = 4  # Downsample
fs_ds = sample_rate / DS


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
    N_fft = 8192  # Zero-padded FFT for high frequency resolution
    sig_sq = sig ** 2
    fft_sq = np.fft.fft(sig_sq, n=N_fft)
    fft_sq[0] = 0  # Remove DC component
    freqs = np.fft.fftfreq(N_fft, d=1/fs_ds)

    # Search for the CFO peak within a reasonable +/- 50 kHz range
    valid_idx = np.where(np.abs(freqs) < 100000)[0]
    if len(valid_idx) == 0:
        return False

    peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
    cfo_est = freqs[peak_idx] / 2.0

    # Generate a complex exponential to completely "de-spin" the buffer
    t = np.arange(len(sig)) / fs_ds
    sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)
    return sig_cfo_corrected


def bit_extraction(sig, phase_offset, start_index, bits_to_extract):
    corrected_sig = sig * np.exp(-1j * phase_offset)

    # Calculate all indices at once
    indices = start_index + np.arange(bits_to_extract) * new_samp

    # Slice the signal and get the real part
    sample_values = np.real(corrected_sig[indices])

    # Convert to '1's and '0's using a list comprehension or join
    bits = ['1' if val > 0 else '0' for val in sample_values]
    return bits


def bit2ascii(bits):
    """
    Converts a list of bit strings ['1', '0', ...] to an ASCII string 
    using vectorized NumPy operations for speed.
    """
    # 1. Convert list of strings ['1', '0'] to a NumPy array of integers [1, 0]
    bit_array = np.array(bits, dtype=np.uint8)

    # 2. Reshape into a matrix where each row is 8 bits (one byte)
    # This allows us to process all bytes simultaneously
    num_bytes = len(bit_array) // 8
    byte_matrix = bit_array[:num_bytes * 8].reshape(-1, 8)

    # 3. Create a vector of powers of 2: [128, 64, 32, 16, 8, 4, 2, 1]
    # We multiply the bits by these weights to get the decimal value
    powers = 2 ** np.arange(7, -1, -1)

    # 4. Dot product: Multiply bits by powers and sum each row
    # This results in an array of integers (0-255)
    ascii_values = np.sum(byte_matrix * powers, axis=1)

    # 5. Filter for printable ASCII (32-126) and convert to string
    decoded_chars = [chr(b) for b in ascii_values if 32 <= b <= 126]

    return "".join(decoded_chars)


new_samp = SAMP_PER_BIT//DS


def receive(sdr: SDR):

    # Pre-calculate Barker sequence parameters
    barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
    barker = np.repeat(barker_base, new_samp)

    # Expected length of message
    EXPECTED_BITS = 80
    required_len = len(barker) + (EXPECTED_BITS * new_samp)

    buffer_size = max(20000, required_len)
    new_buffer = np.zeros(buffer_size, dtype=np.complex64)  # Premade buffer
    wrap_over = []  # initialize for later use

    print("Listening...")
    sdr.start_receive_cont()
    test_var = 0
    while test_var < 100:
        test_var += 1

        sdr.receive_cont_samples(new_buffer)
        new_buffer_ds = new_buffer[::DS]

        buffer = np.concatenate((wrap_over, new_buffer_ds))

        wrap_over = buffer[-required_len:]  # the last part of the buffer for wrapover

        # 1. DC Offset Removal & Normalization
        sig = center_normalize(buffer)
        if isinstance(sig, bool):
            continue  # Skip this loop

        sig_cfo_corrected = frequency_correction(sig)
        if isinstance(sig_cfo_corrected, bool):
            continue  # Skip this loop

        # 3. Frame Synchronization "Detecting" a preample
        corr = np.correlate(sig_cfo_corrected, barker, mode='valid')
        mag_corr = np.abs(corr)

        noise_floor = np.median(mag_corr)
        peak = np.max(mag_corr)

        if peak > 8 * noise_floor:
            indices = np.where(mag_corr > 0.9 * peak)[0]
        else:
            indices = []

        # Group consecutive indices to find local peaks (debouncing)
        if len(indices) > 0:
            # Find gaps between indices to separate different potential packets
            diffs = np.diff(indices)
            starts = np.insert(indices[1:][diffs > len(barker)], 0, indices[0])

            for start_idx in starts:
                # 1. Refine peak within a small window
                window_end = min(start_idx + len(barker), len(mag_corr))
                peak = start_idx + np.argmax(mag_corr[start_idx:window_end])

                # 2. Check boundary
                if peak + required_len < len(sig_cfo_corrected):
                    phase_offset = np.angle(corr[peak])
                    start_bit_idx = peak + len(barker) + (new_samp // 2)

                    bits = bit_extraction(sig_cfo_corrected, phase_offset,
                                          start_bit_idx, EXPECTED_BITS)
                    decoded_msg = bit2ascii(bits)
                    if decoded_msg:
                        print(f"Decoded: {decoded_msg}")


if __name__ == "__main__":
    receive(sdr)
