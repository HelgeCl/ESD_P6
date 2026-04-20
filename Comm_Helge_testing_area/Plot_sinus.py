import numpy as np
import uhd
import matplotlib.pyplot as plt

# --- Configuration ---
scaling = 30
sample_rate = 1e6*scaling    # 1 MHz (Lower is more stable for testing)
center_freq = 5.8e9  # 
tone_freq = 10e3     # 10 kHz (The frequency of the actual beep/tone)
gain = 40            # High gain for B200 antennas
rx_gain = 60
channels = [1]

# --- USRP Setup ---
usrp = uhd.usrp.MultiUSRP()


for chan in channels:
    usrp.set_rx_antenna('TX/RX', chan)
    usrp.set_rx_gain(rx_gain, chan)
    #usrp.set_rx_agc(True, chan) 
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

    #usrp.set_tx_gain(gain, chan)
    usrp.set_tx_rate(sample_rate, chan)
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)



def receive_and_plot(usrp, num_samples=1000):
    # 1. Setup Streamer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = channels
    streamer = usrp.get_rx_stream(st_args)
    
    # 2. Receive Buffer
    buffer = np.zeros((1, num_samples), dtype=np.complex64)
    metadata = uhd.types.RXMetadata()
    
    # Issue stream command
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd.num_samps = num_samples
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)
    
    # Pull data from the USRP
    streamer.recv(buffer, metadata)
    rx_samples = buffer[0]
    
    # 3. Plotting
    plt.figure(figsize=(10, 6))
    
    # Plot Real part (I)
    plt.plot(np.real(rx_samples), label='Real (I)', color='blue')
    # Plot Imaginary part (Q)
    plt.plot(np.imag(rx_samples), label='Imag (Q)', color='red', linestyle='--')
    
    plt.title(f"Received Signal (First {num_samples} samples)")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    #plt.ylim([-1, 1]) # Standard USRP range is -1 to 1
    
    plt.savefig('plot.png', dpi=300, bbox_inches='tight')

# --- RUNNING THE TEST ---
# Ensure your transmitter is running the sinusoid code first!
receive_and_plot(usrp, num_samples=500*scaling)