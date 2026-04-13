import uhd
import numpy as np

# Initialize the USRP
usrp = uhd.usrp.MultiUSRP()

# Parameters
num_samps = 1000000  # 1 million samples
center_freq = 5.8e9    # Center frequency 5.8GHz
sample_rate = 1e6      # 1 Msps (Note: capture will take 1 second)
channels = [0, 1]      # Port 0 and Port 1
gain = 0              # dB

samples = usrp.recv_num_samps(num_samps, center_freq, sample_rate, channels, gain)

np.savez_compressed('usrp_data_from_degree_XX.npz', ch1=samples[0], ch2=samples[1])


