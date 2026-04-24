from Git.ESD_P6.SDR_class import SDR
import numpy as np


SAMPELS_PR_BIT = 32  # Hvor mange samples er der på en bit? I.e. samplerate/SAMPELS_pr_bit = bit rate
SAMPLE_RATE = 1e6
CENTER_FREQ = 5.8e9
GAIN_RX = 60
GAIN_TX = 60

DS = 4  # Downsample by factor
SAMPLE_RATE_DS = SAMPLE_RATE / DS  # Downsampled samplerate
SAMPLES_PR_BIT_DS = SAMPELS_PR_BIT//DS  # Downsampled samples pr. bit

sdr = SDR(SAMPLE_RATE, CENTER_FREQ, GAIN_RX, GAIN_TX, [1])
sdr.setup_receiving()


def center_normalize(sig):
    """Centers and normalizes the signal
    i.e. normalize (sig-mean(sig))
    """
    sig = sig - np.mean(sig)  # Remove DC
    sig_max = np.max(np.abs(sig))
    if sig_max == 0:  # If there is no signal, skip this cycle
        return False
    sig = sig / sig_max  # Normalize to +- 1.0
    return sig


def frequency_correction(sig):
    """
    Correting a signal w.r.t. frequency offset
    """
    # Carrier Frequency Offset (CFO) Correction
    # Required as the transmitter and receiver isnt syncronised on frequency.
    N_fft = 8192  # Size of FFT
    # Squaring BPSK removes the modulation, leaving a tone at 2x the CFO (See report)
    sig_sq = sig ** 2
    fft_sq = np.fft.fft(sig_sq, n=N_fft)
    fft_sq[0] = 0  # Remove DC component
    # While it is technically possible for the signal to be here (if no CFO correction is required), due to the
    # Squaring this is always quite high, especially when remembering, that the SDR has some DC bias.
    # Get frequencies bins who's corresponding magnitude is fft_sq
    freqs = np.fft.fftfreq(N_fft, d=1/SAMPLE_RATE_DS)

    # Search for the CFO peak within +- 50 kHz range (+- 100kHz as we square the signal)
    valid_idx = np.where(np.abs(freqs) < 100000)[0]
    if len(valid_idx) == 0:  # If no frequencies exist (in case of misconfiguration), this just returns before program throws errors
        return False

    # Find the index which corresponds to the maximum signal
    peak_idx = valid_idx[np.argmax(np.abs(fft_sq[valid_idx]))]
    # estimate cfo as this maximum signal (remember to divide the freq by 2, to undo the squaring)
    cfo_est = freqs[peak_idx] / 2.0

    # Correct signal
    t = np.arange(len(sig)) / SAMPLE_RATE_DS
    sig_cfo_corrected = sig * np.exp(-1j * 2 * np.pi * cfo_est * t)  # e^(-j2pi f t)
    return sig_cfo_corrected


def bit_extraction(sig, phase_offset, start_idx, bits_to_extract):
    """Extects bits from signal
    Knowing the start index of the bits
    """
    corrected_sig = sig * np.exp(-1j * phase_offset)  # Correcting the signals phase offset
    # Corrected sig, is now frequency and phase corrected. Meaning that only real signal is left being between -1 and 1.
    # With bit 1 if signal is larger than 0 and 0 if smaller than 0.

    # Calculate the indices of all the bits (As start index is already centered, that is disregarded here)
    indices = start_idx + np.arange(bits_to_extract) * SAMPLES_PR_BIT_DS
    # arange makes an array of 0 to arg. In this case 0 to length of packet

    # As indice has the index of every bit, we can just extact the signal at this index.
    # And as the signal is phase corrected we can just extract the real value
    sample_values = np.real(corrected_sig[indices])

    # Convert to '1's and '0's
    bit_array = (sample_values > 0).astype(np.uint8)  # If true 1, false = 0
    return bit_array


def bit2ascii(bits):
    """
    Converts bits (already in np array) to ascii
    """

    # Make matrix with one byte pr. row
    rows = len(bits) // 8
    byte_matrix = bits[:rows * 8].reshape(-1, 8)
    # Reshape til et 8xN matrix
    # NB :rows * 8 is a satety incase someone uses this fuction without bits being ascii comptaible

    # Vector of powers 2 [128, 64... 2,1] for vector multiplication
    powers = 2 ** np.arange(7, -1, -1)  # arange start, stop (excl.), step

    # matrix (byte), vector (powers) multiplication. Sum each row
    # axis=1, to sum accros rows and not coloums
    ascii_values = np.sum(byte_matrix * powers, axis=1)

    # Convert to ascii
    raw_bytes = bytes(ascii_values.astype(np.uint8))  # Cast into bytes type
    decoded_string = raw_bytes.decode('ascii', errors='ignore')

    return decoded_string


def receive(sdr: SDR, length: int = 80):

    # Calculate barker code:
    barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
    barker = np.repeat(barker_base, SAMPLES_PR_BIT_DS)

    # Package length
    required_len = len(barker) + (length * SAMPLES_PR_BIT_DS)

    buffer_size = max(20000, required_len)
    new_buffer = np.zeros(buffer_size, dtype=np.complex64)  # Premade buffer
    wrap_over = []  # initialize for later use

    sdr.start_receive_cont()
    while True:

        sdr.receive_cont_samples(new_buffer)
        new_buffer_ds = new_buffer[::DS]  # Downsample the received buffer

        buffer = np.concatenate((wrap_over, new_buffer_ds))  # Insert wrap over

        wrap_over = buffer[-required_len:]  # the last part of the buffer for wrapover

        sig = center_normalize(buffer)
        if isinstance(sig, bool):
            continue  # Skip this loop

        sig_cfo_corrected = frequency_correction(sig)
        if isinstance(sig_cfo_corrected, bool):
            continue  # Skip this loop

        # Correlate the signal with the barker code
        corr = np.correlate(sig_cfo_corrected, barker, mode='valid')
        mag_corr = np.abs(corr)  # Magnitude of the complex numbers for comparason

        noise_floor = np.median(mag_corr)
        peak = np.max(mag_corr)

        # len(barker) is the theortical maximum correlation (due to normalization)
        if peak > 6 * noise_floor and peak > (len(barker) * 0.25):
            indices = np.where(mag_corr > 0.9 * peak)[0]
        else:
            indices = []

        # Indices is all index's which correlates well with the barker series
        if len(indices) > 0:  # If indices exist
            # Detect only ONE start for every packet
            # Indices will have a lump of data, then a gap, then a new lump of data.
            # This is due to the barker seires being well correlated for a few samples, then a message, then a new barker comes
            # While also is well correlated

            # The goal is therefore to group these lumps together

            # Find gaps between indices to separate different potential packets
            diffs = np.diff(indices)  # Calculates the difference between two successive elements
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
                    start_bit_idx = peak + len(barker) + (SAMPLES_PR_BIT_DS // 2)
                    # NB this index is places in the center of the samples. This ensures we are measuring in the stable region and not the transision

                    bits = bit_extraction(sig_cfo_corrected, phase_offset,
                                          start_bit_idx, length)
                    decoded_msg = bit2ascii(bits)
                    print(f"Decoded: {decoded_msg}")


if __name__ == "__main__":
    receive(sdr)
