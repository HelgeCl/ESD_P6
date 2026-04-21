import numpy as np
import matplotlib.pyplot as plt

raw_data = np.load("Data/usrp_data_from_degree_-15.npz")


data = np.array([raw_data['RX0'], raw_data['RX1']])


def cal_phase(sig_ch1, sig_ch2):

    # --- Phase Calculation ---
    # We find the angle of the average cross-correlation between the two signals
    # Phase Difference = angle(mean(s1 * conj(s2)))

    phase_diff_rad = np.angle(np.mean(sig_ch1 * np.conj(sig_ch2)))
    phase_diff_deg = np.degrees(phase_diff_rad)

    # print(f"Calculated Phase Difference: {phase_diff_deg:.2f} degrees")
    return (phase_diff_deg)


def plot(sig_ch1, sig_ch2):
    # --- Plotting ---
    plt.figure(figsize=(12, 6))

    # Plot Real part (I) of both channels to see the sinusoids
    plt.plot(np.real(sig_ch1), label='Channel 1 (Real)', alpha=0.8)
    plt.plot(np.real(sig_ch2), label='Channel 2 (Real)', alpha=0.8, linestyle='--')

    plt.title(f"Received Sinusoids")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)

    # plt.savefig('dual_channel_plot.png', dpi=300, bbox_inches='tight')
    plt.show()


total_phase = cal_phase(data[0], data[1])
print(total_phase)


results = []
window_size = 10000
for i in range(len(data[0]) - window_size + 1):
    window = data[:, i: i + window_size]
    results.append(cal_phase(window[0], window[1]))

plot(results, results)

print(np.max(results), np.mean(results), np.min(results))
