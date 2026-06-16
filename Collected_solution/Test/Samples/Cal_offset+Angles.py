
import matplotlib.pyplot as plt
import numpy as np


class find_samps:
    def __init__(self):
        self.barker_base = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
        samples_pr_bit = 16
        sample_rate = 500e3
        self.ds = 2
        self.sample_rate_ds = sample_rate / self.ds
        self.samples_pr_bit_ds = samples_pr_bit // self.ds

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
        return sig_cfo_corrected, cfo_est

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

    def correct_and_find_starts(self, buffer, barker):
        sig = self.__center_normalize(buffer)
        if isinstance(sig, bool):
            return None

        sig_cfo_corrected, cfo_est = self.__frequency_correction(sig)
        if isinstance(sig_cfo_corrected, bool):
            return None

        # Correlate the signal with the barker code
        corr = np.correlate(sig_cfo_corrected, barker)
        mag_corr = np.abs(corr)  # Magnitude of the complex numbers for comparason

        noise_floor = np.median(mag_corr)
        peak_corr = np.max(mag_corr)

        # len(barker) is the theortical maximum correlation (due to normalization)
        if peak_corr > 2 * noise_floor and peak_corr > (len(barker) * 0.55):
            indices = np.where(mag_corr > 0.9 * peak_corr)[0]
        else:
            indices = []

        # Indices is all index's which correlates well with the barker series
        if len(indices) == 0:
            return None

        return indices, sig_cfo_corrected, mag_corr, corr, cfo_est

    def receive(self, full_2D_buffer, length: int = 256):

        # Calculate barker code:
        barker = np.repeat(self.barker_base, self.samples_pr_bit_ds)

        # Package length
        required_len = len(barker) + (length * self.samples_pr_bit_ds)

        new_buffer = full_2D_buffer[0, :]
        new_buffer_ds = new_buffer[::self.ds]  # Downsample the received buffer
        corrected_data = self.correct_and_find_starts(new_buffer_ds, barker)
        indices, sig_cfo_corrected, mag_corr, corr, cfo_est = corrected_data
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
                rtn.append(
                    (bits, (full_2D_buffer[:, peak*self.ds:(peak+length)*self.ds], cfo_est, phase_offset)))
        if rtn != []:  # Sanity check
            return rtn


ALL_SIM_ANGLES = [-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90]
ANGLES = [-60, -45, -30, -15, 0, 15, 30, 45, 60]
ANGLES = [0, 15, 30, 45]

MEASURED_FILES = [
    "combined_data_60dB.npz",
    "combined_data_50dB.npz",
    "combined_data_40dB.npz"
]


def plot(val):
    # 3. Plotting
    plt.figure(figsize=(10, 6))

    plt.plot(val, label='Abs CH1', color='blue')
    # Plot Imaginary part (Q)
    # plt.plot(np.abs(sampes[1]), label='Abs CH2', color='red', linestyle='--')

    plt.title(f"Received Signal")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    # plt.ylim([-1, 1]) # Standard USRP range is -1 to 1

    # plt.savefig('plot.png', dpi=300, bbox_inches='tight')
    plt.show()


# file = np.load("combined_data_60dB.npz")
# plot(abs(file["angle_0_0"]))
# exit()

# 0, 15, 30, 45
recv = find_samps()

m_data = np.load("combined_data_60dB.npz")

key = f"angle_0"
angle_data_0 = m_data[key+"_0"]
angle_data_1 = m_data[key+"_1"]
buffer = np.vstack((angle_data_0, angle_data_1))

out = recv.receive(buffer)
bits = [packet[0] for packet in out]
data = [packet[1] for packet in out]

buf = [packet[0] for packet in data]
cfo = [packet[1] for packet in data]
phase = [packet[2] for packet in data]

buffer = np.vstack((angle_data_1, angle_data_0))
out_1 = recv.receive(buffer)

bits_1 = [packet[0] for packet in out_1]
data_1 = [packet[1] for packet in out_1]

buf_1 = [packet[0] for packet in data_1]
cfo_1 = [packet[1] for packet in data_1]
phase_1 = [packet[2] for packet in data_1]

phases = []
for idx, _ in enumerate(phase):
    try:
        phases.append(phase[idx]-phase_1[idx])
    except:
        break

print(phases)
print(np.max(phases), np.mean(phases), np.min(phases))


exit()
for i, file_name in enumerate(MEASURED_FILES):
    try:
        # 1. Process Measured Data (Dynamic lookup based on ANGLES)
        m_data = np.load(file_name)
        for ang in ANGLES:
            key = f"angle_{ang}"
            angle_data_0 = m_data[key+"_0"]
            angle_data_1 = m_data[key+"_1"]
            buffer = np.vstack((angle_data_0, angle_data_1))
            recv.receive(buffer)

    except FileNotFoundError:
        print(f"Warning: {file_name} not found.")


def esprit_correction(esprit_data):
    # sig_cfo = sig * np.exp(-1j * 2 * np.pi * cfo * t)
    # sig_cfo_phase = sig_cfo * np.exp(-1j * phase_offset)
    sig, cfo, phase_offset = esprit_data
    num_samples = sig.shape[1]
    t = np.arange(num_samples)
    return sig * np.exp(-1j * (2 * np.pi * cfo * t + phase_offset))
