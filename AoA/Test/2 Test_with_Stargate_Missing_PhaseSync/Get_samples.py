import uhd
import numpy as np
from Git.ESD_P6.AoA.Speed_test.DoA import esprit

# Initialize the USRP
usrp = uhd.usrp.MultiUSRP()



# Parameters
num_samps = 100000  # 1 million samples
center_freq = 5.8e9    # Center frequency 5.8GHz
sample_rate = 1e6      # 1 Msps (Note: capture will take 1 second)
channels = [0, 1]      # Port 0 and Port 1
gain = 30              # dB

usrp.set_clock_source('internal')
for chan in channels:
    usrp.set_rx_antenna('RX2', chan) # Switch from TX/RX to RX2
    usrp.set_rx_gain(gain, chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

samples = usrp.recv_num_samps(num_samps, center_freq, sample_rate, channels, gain)


set = samples[:,:200]
print(set.shape)
print("angle: ", esprit(set.T, len(set)))

peak_signal = np.max(np.abs(samples))
print("Max val:", peak_signal)
n = 0.001450191
print("Snr: ", 20 * np.log10(peak_signal / n))

np.savez_compressed('Git/ESD_P6/AoA/Test_with_Stargate/usrp_data_from_degree_XX.npz', ch1=samples[0], ch2=samples[1])


