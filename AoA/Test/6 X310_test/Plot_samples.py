import numpy as np
import matplotlib.pyplot as plt

# 1. Load the data


#data = np.load('Git/ESD_P6/AoA/usrp_data_from_degree_XX.npz')
data = np.load('Git/ESD_P6/AoA/X310_2.npz')
n_zoom = 10000 #Max 1000000


ch1 = data['ch1']
ch2 = data['ch2']

# 2. Settings (Adjust these based on your actual capture)
fs = 1e6  # Sample rate: 100 MHz
t = np.arange(len(ch1)) / fs

# 3. Create the Visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# --- Top Plot: Time Domain (Magnitude) ---
# We plot the first 500 samples to see the waveform clearly
 
ax1.plot(t[:n_zoom] * 1e6, ch2[:n_zoom].real, label='Channel 2 (real)')
#ax1.plot(t[:n_zoom] * 1e6, np.abs(ch2[:n_zoom]), label='Channel 2', alpha=0.7)
ax1.plot(t[:n_zoom] * 1e6, ch1[:n_zoom].real, label='Channel 1 (Real)')
#ax1.plot(t[:n_zoom] * 1e6, ch1[:n_zoom].imag, label='Channel 1 (Imag)', alpha=0.7)
ax1.set_title(r'Time Domain: Signal Magnitude (First $500$ samples)')
ax1.set_xlabel(r'Time ($\mu s$)')
ax1.set_ylabel(r'Magnitude')
ax1.legend()
ax1.grid(True)

# --- Bottom Plot: Frequency Domain (PSD) ---
ax2.psd(ch1, NFFT=1024, Fs=fs/1e6, label='Channel 1')
ax2.psd(ch2, NFFT=1024, Fs=fs/1e6, label='Channel 2')
ax2.set_title(r'Frequency Domain: Power Spectral Density')
ax2.set_xlabel(r'Frequency ($MHz$)')
ax2.set_ylabel(r'Power ($dB/Hz$)')
ax2.legend()

plt.tight_layout()
plt.savefig('plot.png', dpi=300, bbox_inches='tight')