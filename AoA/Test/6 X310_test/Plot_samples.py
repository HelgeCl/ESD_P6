import numpy as np
import matplotlib.pyplot as plt

# 1. Load the data


# data = np.load('Git/ESD_P6/AoA/usrp_data_from_degree_XX.npz')
data = np.load('X310_1.npz')
n_zoom = 10000  # Max 1000000


ch1 = data['ch1']
ch2 = data['ch2']

# 2. Settings (Adjust these based on your actual capture)
fs = 1e6  # Sample rate: 100 MHz
t = np.arange(len(ch1)) / fs

# 3. Create the Visualization
plt.figure(figsize=(6, 4))

# --- Top Plot: Time Domain (Magnitude) ---
# We plot the first 500 samples to see the waveform clearly

plt.plot(t[:n_zoom] * 1e6, ch2[:n_zoom].real, label='Channel 2 (real)')
# ax1.plot(t[:n_zoom] * 1e6, np.abs(ch2[:n_zoom]), label='Channel 2', alpha=0.7)
plt.plot(t[:n_zoom] * 1e6, ch1[:n_zoom].real, label='Channel 1 (Real)')
# ax1.plot(t[:n_zoom] * 1e6, ch1[:n_zoom].imag, label='Channel 1 (Imag)', alpha=0.7)
plt.title(r'Timeplot of first $10000$ samples')
plt.xlabel(r'Time ($\mu s$)')
plt.ylabel(r'Magnitude')
plt.legend()
plt.grid(True)


plt.tight_layout()
plt.savefig('plot1.png', dpi=300, bbox_inches='tight')
