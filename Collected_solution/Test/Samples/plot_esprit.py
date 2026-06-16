import numpy as np
import matplotlib.pyplot as plt

# matplotlib.use('Agg')

# --- Configuration ---
# Define the full range used during simulation to find the correct indices
ALL_SIM_ANGLES = [-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90]
# Select the specific subset you want to plot
# -90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90
ANGLES = [-60, -45, -30, -15, 0, 15, 30, 45, 60]

MEASURED_FILES = [
    "combined_angles_40dB.npz",
    "combined_angles_50dB.npz",
    "combined_angles_60dB.npz"
]
STD_TARGET = 0.2884
GAINS = [40, 50, 60]

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
    label_base = GAINS[i]
    try:
        # 1. Process Measured Data (Dynamic lookup based on ANGLES)
        m_data = np.load(file_name)

        m_stds, m_means = [], []
        for ang in ANGLES:
            key = f"angle_{ang}"
            if key in m_data:
                estimates = -m_data[key]
                m_means.append(np.mean(estimates - ang))
                m_stds.append(np.std(estimates - ang))
            else:
                m_means.append(np.nan)
                m_stds.append(np.nan)

        # Plot Measured
        ax1.plot(ANGLES, m_stds, color=colors[i], marker='o', markersize=5, lw=1.5,
                 label=f"TX gain {label_base}")
        ax2.plot(ANGLES, m_means, color=colors[i], marker='s', markersize=5, lw=1.5,
                 label=f"TX gain {label_base}")

    except FileNotFoundError:
        print(f"Warning: {file_name} not found.")

# --- Formatting Updates ---
ax1.axhline(y=STD_TARGET, color='black', linestyle=':', alpha=0.6)
ax1.set_yscale('log')
ax1.set_ylabel('Standard Deviation (Deg)')
ax1.set_title('ESPRIT Precision Measured', fontweight='bold')
ax1.grid(True, which="both", color='#F0F0F0', linestyle='-')
ax1.set_ylim(10**-2, 10**2)  # Adjusted for "Zoomed" view

ax2.axhline(y=0, color='black', lw=1, alpha=0.3)
ax2.set_ylabel('Mean Error (Deg)')
ax2.set_xlabel('True Angle (Deg)')
ax2.set_title('ESPRIT Accuracy Measured', fontweight='bold')
ax2.grid(True, color='#F0F0F0')

ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=True, fontsize=8)

# Set limits slightly wider than the chosen ANGLES for visual breathing room
ax1.set_xlim(min(ANGLES)-5, max(ANGLES)+5)
ax1.set_xticks(ANGLES)

plt.tight_layout()
plt.show()
# plt.savefig("esprit_comparison_overlay_Zoomed.png", dpi=300, bbox_inches='tight')
