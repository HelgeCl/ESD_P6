import numpy as np
import uhd
import matplotlib.pyplot as plt
import time


# --- Configuration ---
scaling = 30
sample_rate = 1e6 * scaling    # 30 MHz
center_freq = 5.8e9  
rx_gain = 60
channels = [0, 1]              # Receive on both Channel 0 and 1

# --- USRP Setup ---
usrp = uhd.usrp.MultiUSRP()

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

def plot(sig_ch1, sig_ch2):
    # --- Plotting ---
    plt.figure(figsize=(12, 6))
    
    # Plot Real part (I) of both channels to see the sinusoids
    plt.plot(np.real(sig_ch1), label='Channel 1 (Real)', alpha=0.8)
    plt.plot(np.real(sig_ch2), label='Channel 2 (Real)', alpha=0.8, linestyle='--')
    
    plt.title(f"Received Sinusoids")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    
    plt.savefig('dual_channel_plot.png', dpi=300, bbox_inches='tight')
    #plt.show()

def receive_and_plot(usrp, num_samples):
    ch1, ch2 = receive(usrp, num_samples)
    cal_phase(ch1, ch2)
    plot(ch1, ch2)

def receive_and_calc(usrp,num_samples):
    ch1, ch2 = receive(usrp, num_samples)
    return(cal_phase(ch1, ch2))

# --- RUNNING THE TEST ---

time.sleep(10)

"""for chan in channels:
    usrp.set_rx_antenna('TX/RX', chan)
    #usrp.set_rx_antenna('RX2', chan)



for chan in channels:
    usrp.set_rx_antenna('RX2', chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
    usrp.set_rx_gain(rx_gain, chan)


"""
samples = []
for _ in range(0,100):
    #input("Enter for next measuremnet")
    samples.append(receive_and_calc(usrp, num_samples=500*scaling))


print(np.max(samples), np.mean(samples), np.min(samples))

rx_correction = 46.620819065443165-np.mean(samples)


print(rx_correction)


#usrp.set_rx_antenna('TX/RX', 1)
for chan in channels:
    usrp.set_rx_antenna('TX/RX', chan)
    #usrp.set_rx_antenna('RX2', chan)

#for chan in channels:
#    usrp.set_rx_antenna('RX2', chan)



#Med fire udgange
#To correct for different phase due to the system, 
# RX2(0) -> TX/RX(0) Forskel er 45.158966892755515
# -> På SDR ses mean på cirka -50 (fra mean 48.03264 til -8.699985)
# Dette giver mening da dette er "referencen" til phase skift der skiftes, frem, så ryger denne tilbage
#RX2(1) -> TX/RX(1) forskel er -23.116905816387995
# -> På SDR ses mean på cirka -13 (fra mean 48.036915 til 35.027954)
# det giver mening da hvis denne bevæger sig tilbage, betyder det direkte at faseskiftet bliver mere negativt.

#Skift af begge:
#Fra 48.413544
#-21.61941

#Altså for ikke at give en faseforskel med de 4 kabel, bør



#Indgang Rx får et faseskiftet signal på 46.620819065443165
# Påstår det er -39.878494

#RX er altså off med 86.4993130654

#indgang RX/TX får et faseskiftet signal på 7.289298620442004
# Påstår det er -27.187168



# Altså må korrektionen mellem rx og tx være 52.022846445


"""
Inital:
-39.784813 -39.938133 -40.0792
86.55895
-26.742617 -27.099869 -27.578753
7.4362373

Restart 1:
-36.566288 -36.66254 -36.757107
83.283356
-24.01424 -24.266052 -24.556728
6.9944572

Restart 2:
-37.10946 -37.18045 -37.24522
83.80127
-24.360004 -24.579834 -24.818663
7.1985893

Restart 3:
-37.115196 -37.169533 -37.230896
83.79035
-24.437756 -24.621103 -24.830524
7.1464043

Restart 4:
-39.79119 -39.96532 -40.122955
86.586136
-27.049683 -27.41735 -27.80306
7.145939

Restart 5:
-37.182945 -37.391945 -37.669746
84.012764
-23.435322 -24.000334 -25.79568
7.989582

Restart 6:
-34.50415 -38.949574 -41.505917
85.57039
-25.578583 -25.907444 -26.217466
7.6400986
"""




samples = []
for _ in range(0,100):
    #input("Enter for next measuremnet")
    samples.append(receive_and_calc(usrp, num_samples=500*scaling))


print(np.max(samples), np.mean(samples), np.min(samples))

print(np.mean(samples)+rx_correction-52.022846445)
