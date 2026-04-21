import numpy as np
import matplotlib.pyplot as plt

# raw_data = np.load("Baseline/Baseline_2.npz")
raw_data = np.load("Data/usrp_data_from_degree_-15.npz")

RX_data = np.array([raw_data['RX0'], raw_data['RX1']])
TX_data = np.array([raw_data['RX_TX0'], raw_data['RX_TX1']])


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


plot(RX_data[0], RX_data[1])
plot(TX_data[0], TX_data[1])

results_rx = []
window_size = 10000
for i in range(len(RX_data[0]) - window_size + 1):
    window = RX_data[:, i: i + window_size]
    results_rx.append(cal_phase(window[0], window[1]))

results_tx = []
window_size = 10000
for i in range(len(TX_data[0]) - window_size + 1):
    window = TX_data[:, i: i + window_size]
    results_tx.append(cal_phase(window[0], window[1]))


plot(results_rx, results_tx)

# print(np.max(results), np.mean(results), np.min(results))
