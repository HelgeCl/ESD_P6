import numpy as np
import uhd
import matplotlib.pyplot as plt
import time
from Git.ESD_P6.AoA.DoA import esprit

# --- Configuration ---
scaling = 30
sample_rate = 1e6    # 30 MHz
center_freq = 5.8e9  
rx_gain = 100
channels = [0, 1]              # Receive on both Channel 0 and 1

# --- USRP Setup ---
usrp = uhd.usrp.MultiUSRP("addr0=192.168.30.2, num_recv_frames=512")


for chan in channels:
    #usrp.set_rx_antenna('TX/RX', chan)
    usrp.set_rx_antenna('RX2', chan)

    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
    usrp.set_rx_gain(rx_gain, chan)

num_samples=500*scaling
# 1. Setup Streamer
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = channels
st_args.args = uhd.types.DeviceAddr("spp=368")
streamer = usrp.get_rx_stream(st_args)

# 2. Receive Buffer
buffer = np.zeros((len(channels), num_samples), dtype=np.complex64)
metadata = uhd.types.RXMetadata()

# --- FIX: Synchronized Stream Command ---
stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
stream_cmd.num_samps = num_samples
stream_cmd.stream_now = False  # Set to False to allow timing

usrp.set_clock_source("internal")
usrp.set_time_source("internal")
usrp.set_time_now(uhd.types.TimeSpec(0.0))
usrp.set_time_unknown_pps(uhd.types.TimeSpec(0.0))
time.sleep(1) # Give it a second to lock

def receive(usrp, num_samples=1000):

    
    # Set the start time to 0.1 seconds in the future
    # This allows the command to reach both radio chains simultaneously
    seconds_to_delay = 0.1
    stream_cmd.time_spec = usrp.get_time_now() + uhd.types.TimeSpec(seconds_to_delay)
    
    streamer.issue_stream_cmd(stream_cmd)
    # ----------------------------------------
    
    # Pull data
    streamer.recv(buffer, metadata)
    
    sig_ch1 = buffer[0]
    sig_ch2 = buffer[1]
    
    return sig_ch1, sig_ch2

def cal_phase(sig_ch1, sig_ch2):
    
    # --- Phase Calculation ---
    # We find the angle of the average cross-correlation between the two signals
    # Phase Difference = angle(mean(s1 * conj(s2)))
    
    phase_diff_rad = np.angle(np.mean(sig_ch1 * np.conj(sig_ch2)))
    phase_diff_deg = np.degrees(phase_diff_rad)
    
    #print(f"Calculated Phase Difference: {phase_diff_deg:.2f} degrees")
    return(phase_diff_deg)


for _ in range(0,100):
    offset = 100 
    samples = receive(usrp, 1000000+offset)
    #Offset to discard the first samples

    samples = np.array(samples, dtype=np.complex64)
    samples = samples[:, offset:]
    set = samples[:,:200]
    #print("angle: ", esprit(set.T, 1))
    print(np.max(np.abs(samples[0])))
    print("phaseoffset: ", cal_phase(samples[0], samples[1]))


peak_signal = np.max(np.abs(samples))
print("Max val:", peak_signal)
n = 0.001450191
print("Snr: ", 20 * np.log10(peak_signal / n))

np.savez_compressed('Git/ESD_P6/AoA/usrp_data_from_degree_XX.npz', ch1=samples[0], ch2=samples[1])


