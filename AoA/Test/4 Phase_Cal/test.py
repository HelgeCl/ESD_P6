from scipy.signal import hilbert
import numpy as np
import matplotlib.pyplot as plt
import time


import pandas as pd

# Define a function to handle the specific CSV structure


def load_scope_csv(file_path):
    # 'skiprows' might be needed if there is header metadata at the top
    # 'usecols' selects only the 'time' and 'amplitude' columns
    df = pd.read_csv(file_path, names=['col1', 'col2', 'col3', 'time', 'amplitude'])
    return df[['time', 'amplitude']]


# Loading each channel
ch1 = load_scope_csv('Blå1.csv')
ch2 = load_scope_csv('Blå2.csv')
ch3 = load_scope_csv('Sort1.csv')
ch4 = load_scope_csv('Sort2.csv')


def cal_phase(sig_ch1, sig_ch2):
    # 1. Convert real signals to analytic (complex) signals
    # This creates a complex signal where the real part is your data
    # and the imaginary part is the Hilbert transform.
    z1 = hilbert(sig_ch1)
    z2 = hilbert(sig_ch2)

    # 2. Calculate the phase difference for every point
    # We multiply z1 by the complex conjugate of z2
    # The angle of the mean of these products gives the average phase shift
    phase_diff_rad = np.angle(np.mean(z1 * np.conj(z2)))

    return np.degrees(phase_diff_rad)


print(cal_phase(ch2["amplitude"], ch1["amplitude"]))  # Byttet da RF 0 er ref
print(cal_phase(ch3["amplitude"], ch4["amplitude"]))
# print(cal_phase(ch1["amplitude"], ch4["amplitude"]))


# Blå kabler:
# 1 =23
# 2 = 34
# Kopper kabler:
# 1 = 59
# 2 = 41
# Sort
# 1 = 54
# 2 = 12


# Jeg skal altså gerne se en faseforskel på:
# 46.620819065443165 ved RX
# 7.289298620442004 ved RX/TX
