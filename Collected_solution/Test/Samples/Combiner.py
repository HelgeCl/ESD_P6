import os
import numpy as np

# List of angles you have
angles = [-60, -45, -30, -15, 0, 15, 30, 45, 60]

combined_data = {}

for angle in angles:
    filename = f"60dB_gain/data_from_degree_{angle}.npz"

    if os.path.exists(filename):
        # Load the file
        with np.load(filename) as data:
            # Assuming each file has one primary array, or you want the whole dict.
            # If your files have specific internal keys (like 'data'), extract it:
            # combined_data[f"angle_{angle}"] = data['data']

            # Otherwise, if it's just a single unnamed array saved by np.savez:
            key = list(data.keys())[0]
            combined_data[f"angle_{angle}_0"] = data[key]
            key = list(data.keys())[1]
            combined_data[f"angle_{angle}_1"] = data[key]
    else:
        print(f"Warning: {filename} not found.")

# Save everything into a single consolidated .npz file
np.savez("combined_data_60dB.npz", **combined_data)
print("Files successfully combined into 'combined_data.npz'!")
