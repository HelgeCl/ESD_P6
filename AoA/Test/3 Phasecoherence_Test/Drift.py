"""Drift er ikke et problem, når først vi venter 20 sekunder fra bootup
-13.50304 -13.700962 -13.875379
max, mean, min


Setup, RX2 på kanal 0 og 1 med to kabel og A6-215-C-8 1017-00 power splitter, og Signal generator -40dBm, 5.8GHz
Målt på digital phosphor oscilloscope til ikke at have en notable faseforskel

ved at køre dette script:"""

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
    # usrp.set_rx_antenna('TX/RX', chan)
    usrp.set_rx_antenna('RX2', chan)

    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)
    usrp.set_rx_gain(rx_gain, chan)


num_samples = 500*scaling
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
time.sleep(1)  # Give it a second to lock


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

    # print(f"Calculated Phase Difference: {phase_diff_deg:.2f} degrees")
    return (phase_diff_deg)


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
    # plt.show()


def receive_and_plot(usrp, num_samples):
    ch1, ch2 = receive(usrp, num_samples)
    cal_phase(ch1, ch2)
    plot(ch1, ch2)


def receive_and_calc(usrp, num_samples):
    ch1, ch2 = receive(usrp, num_samples)
    return (cal_phase(ch1, ch2))

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
for _ in range(0, 200):
    # input("Enter for next measuremnet")
    samples.append(receive_and_calc(usrp, num_samples=500*scaling))


print(np.max(samples), np.mean(samples), np.min(samples))
