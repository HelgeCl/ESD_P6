import numpy as np
import matplotlib.pyplot as plt
import time


raw_data = np.load("RXTX_data_10e7.npz")

RX_data = np.array([raw_data['RX0'], raw_data['RX1']])
TX_data = np.array([raw_data['RX_TX0'], raw_data['RX_TX1']])

RX_data = RX_data[:, :1000]
TX_data = TX_data[:, :1000]


def cal_phase(sig_ch1, sig_ch2):

    # --- Phase Calculation ---
    # We find the angle of the average cross-correlation between the two signals
    # Phase Difference = angle(mean(s1 * conj(s2)))

    phase_diff_rad = np.angle(np.mean(sig_ch1 * np.conj(sig_ch2)))
    phase_diff_deg = np.degrees(phase_diff_rad)

    # print(f"Calculated Phase Difference: {phase_diff_deg:.2f} degrees")
    return (phase_diff_deg)


def plot(sig_ch1, sig_ch2, name: str = "name"):
    # --- Plotting ---
    plt.figure(figsize=(6, 4))

    # Plot Real part (I) of both channels to see the sinusoids
    plt.plot(np.real(sig_ch1), label='Channel 1 (Real)', alpha=0.8)
    plt.plot(np.real(sig_ch2), label='Channel 2 (Real)', alpha=0.8, linestyle='--')

    plt.title(f"Received Sinusoids")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend(loc="best")
    plt.grid(True)

    plt.savefig(str(name)+'.png', dpi=300, bbox_inches='tight')
    # plt.show()


plot(RX_data[0], RX_data[1], "RX_first_off")
plot(TX_data[0], TX_data[1], "TX_first_off")

exit()

results_rx = []
window_size = 100
for i in range(len(RX_data[0]) - window_size + 1):
    window = RX_data[:, i: i + window_size]
    results_rx.append(cal_phase(window[0], window[1]))


results_tx = []
window_size = 100
for i in range(len(TX_data[0]) - window_size + 1):
    window = TX_data[:, i: i + window_size]
    results_tx.append(cal_phase(window[0], window[1]))

print("RX:", np.max(results_rx), np.mean(results_rx), np.min(results_rx))
print("TX:", np.max(results_tx), np.mean(results_tx), np.min(results_tx))

plot(results_rx, results_tx, "name")
