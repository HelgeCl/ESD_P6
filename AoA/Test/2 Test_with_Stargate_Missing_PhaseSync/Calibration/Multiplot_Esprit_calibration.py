import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')

# --- Configuration ---
# Define the full range used during simulation to find the correct indices
ALL_SIM_ANGLES = [-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90]
# Select the specific subset you want to plot
# -90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90
ANGLES = [-30, -15, 0, 15, 30]

MEASURED_FILES = [
    "esprit_all_results_0dBm_cal.npz",
    "esprit_all_results_-9dBm_cal.npz",
    "esprit_all_results_-20dBm_cal.npz"
]
SIM_SNR_KEYS = ["32", "23.1", "12"]
STD_TARGET = 0.2884

# Identify indices in simulation data that match our chosen ANGLES
# This prevents dimension mismatch errors
sim_indices = [ALL_SIM_ANGLES.index(a) for a in ANGLES]

# Setup Figure
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 9), sharex=True)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

try:
    sim_data = np.load("esprit_simulated_results.npz")
except FileNotFoundError:
    print("Simulation file not found.")
    sim_data = None

for i, file_name in enumerate(MEASURED_FILES):
    try:
        # 1. Process Measured Data (Dynamic lookup based on ANGLES)
        m_data = np.load(file_name)
        measured_snr = np.mean(m_data['SNR_degree_0'])

        m_stds, m_means = [], []
        for ang in ANGLES:
            key = f"degree_{ang}"
            if key in m_data:
                estimates = m_data[key]
                m_means.append(np.mean(estimates - ang))
                m_stds.append(np.std(estimates - ang))
            else:
                m_means.append(np.nan)
                m_stds.append(np.nan)

        label_base = f"{measured_snr:.1f} dB SNR"

        # Plot Measured
        ax1.plot(ANGLES, m_stds, color=colors[i], marker='o', markersize=5, lw=1.5,
                 label=f"Measured ({label_base})")
        ax2.plot(ANGLES, m_means, color=colors[i], marker='s', markersize=5, lw=1.5,
                 label=f"Measured ({label_base})")

        # 2. Process Simulated Data (Filtered by sim_indices)
        if sim_data is not None:
            std_key, mu_key = f"std_{SIM_SNR_KEYS[i]}", f"mu_{SIM_SNR_KEYS[i]}"

            if std_key in sim_data:
                # Extract only the values at the indices corresponding to ANGLES
                sim_stds_filtered = sim_data[std_key][sim_indices]
                sim_means_filtered = sim_data[mu_key][sim_indices]

                ax1.plot(ANGLES, sim_stds_filtered, color=colors[i], linestyle='--',
                         lw=2, alpha=0.6, label=f"Simulated ({SIM_SNR_KEYS[i]} dB)")
                ax2.plot(ANGLES, sim_means_filtered, color=colors[i], linestyle='--',
                         lw=2, alpha=0.6, label=f"Simulated ({SIM_SNR_KEYS[i]} dB)")

    except FileNotFoundError:
        print(f"Warning: {file_name} not found.")

# --- Formatting Updates ---
ax1.axhline(y=STD_TARGET, color='black', linestyle=':', alpha=0.6)
ax1.set_yscale('log')
ax1.set_ylabel('Standard Deviation (Deg)')
ax1.set_title('ESPRIT Precision: Measured vs Simulated', fontweight='bold')
ax1.grid(True, which="both", color='#F0F0F0', linestyle='-')
ax1.set_ylim(10**-2, 10**2)  # Adjusted for "Zoomed" view

ax2.axhline(y=0, color='black', lw=1, alpha=0.3)
ax2.set_ylabel('Mean Error (Deg)')
ax2.set_xlabel('True Angle (Deg)')
ax2.set_title('ESPRIT Accuracy: Measured vs Simulated', fontweight='bold')
ax2.grid(True, color='#F0F0F0')

ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=True, fontsize=8)

# Set limits slightly wider than the chosen ANGLES for visual breathing room
ax1.set_xlim(min(ANGLES)-5, max(ANGLES)+5)
ax1.set_xticks(ANGLES)

plt.tight_layout()
plt.savefig("esprit_comparison_overlay_Calibrated.png", dpi=300, bbox_inches='tight')
