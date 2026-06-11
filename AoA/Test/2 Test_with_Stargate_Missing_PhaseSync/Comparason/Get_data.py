import numpy as np

# --- Configuration ---
# Define the full range used during simulation to find the correct indices
ALL_SIM_ANGLES = [-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90]
# Select the specific subset you want to plot
ANGLES = [-45, -30, -15, 0, 15, 30, -45]  # -90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90

MEASURED_FILES = [
    "esprit_all_results_0dBm.npz",
    "esprit_all_results_-9dBm.npz",
    "esprit_all_results_-20dBm.npz"
]


results_data = np.load(MEASURED_FILES[0])

results = []

# Access a specific result
for item in ANGLES:
    results.append(results_data['degree_'+str(item)])


print(np.max(results))

print(np.min(results))
