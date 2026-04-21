import numpy as np

data = np.load('CableCal.npz')


ch1 = data['ch1']
ch2 = data['ch2']

x0 = ch1
x1 = ch2

# Calculate the complex scaling factor (Phasor)
# This represents how x1 relates to x0: x1 = H * x0
H = np.sum(x1 * np.conj(x0)) / np.sum(x0 * np.conj(x0))

# Extract Gain and Phase
gain_factor = np.abs(H)
phase_rad = np.angle(H)

print(gain_factor)
print(np.rad2deg(phase_rad))


# Pi 2 resultere i:
# gain 0.9793722
# phase 0.17607468
