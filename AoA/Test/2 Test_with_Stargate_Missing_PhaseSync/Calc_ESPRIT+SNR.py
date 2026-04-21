import numpy as np
import os
from glob import glob
from DoA import esprit

# --- Settings ---
folder_path = '0dBm/'
baseline_path = 'Baseline_Nul_signal.npz'
output_filename = 'esprit_all_results_0dBm.npz'
window_size = 200

# 1. Load Baseline and Calculate Noise Power once
baseline_raw = np.load(baseline_path)
data_baseline = np.array([baseline_raw['ch1'], baseline_raw['ch2']])
p_noise = np.mean(np.abs(data_baseline)**2)

# 2. Identify all .npz files in the target folder
# This matches all files starting with 'usrp_data'
files = glob(os.path.join(folder_path, "usrp_data_from_degree_*.npz"))

# This dictionary will store our results { 'degree_0': [angles...], 'SNR_degree_0': 14.2 }
all_storage = {}

print(f"Found {len(files)} files. Starting processing...")

for file_path in files:
    # Extract a clean name for the dictionary key (e.g., 'degree_0')
    file_name = os.path.basename(file_path).replace('usrp_data_from_', '').replace('.npz', '')

    print(f"Processing {file_name}...")

    # Load and format data
    raw_data = np.load(file_path)
    data = np.array([raw_data['ch1'], raw_data['ch2']])

    # Calculate SNR
    p_signal_plus_noise = np.mean(np.abs(data)**2)
    p_signal_only = max(p_signal_plus_noise - p_noise, 1e-12)
    snr_db = 10 * np.log10(p_signal_only / p_noise)

    # Run Sliding Window ESPRIT
    total_samples = data.shape[1]
    results = []

    for i in range(total_samples - window_size + 1):
        window = data[:, i: i + window_size]
        angle = esprit(window, 1).item()
        results.append(angle)

    # Save both the array of angles and the SNR to our storage dict
    all_storage[file_name] = np.array(results)
    all_storage[f"SNR_{file_name}"] = snr_db

# 3. Save everything into one single file
np.savez(output_filename, **all_storage)
print(f"\nDone! All results saved to {output_filename}")
