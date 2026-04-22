import numpy as np
import uhd
import matplotlib.pyplot as plt

# --- Configuration ---
scaling = 1
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
    
    #plt.savefig('plot.png', dpi=300, bbox_inches='tight')
    plt.show()


def receive_and_plot_FFT(usrp, num_samples=1000, sample_rate=1e6):
        
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
    
    # --- Frequency Domain Processing ---
    # Apply a window (like Hamming) to reduce spectral leakage
    window = np.hamming(num_samples)
    fft_data = np.fft.fft(rx_samples * window)
    fft_shifted = np.fft.fftshift(fft_data)
    
    # Calculate Magnitude in dB
    # We add a tiny epsilon to avoid log10(0)
    mag_db = 20 * np.log10(np.abs(fft_shifted) + 1e-12)
    
    # Frequency axis centered around 0 (relative to Carrier Frequency)
    freqs = np.linspace(-sample_rate/2, sample_rate/2, num_samples)

    # 3. Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    
    # Time Domain Plot
    ax1.plot(np.real(rx_samples), label='Real (I)', color='blue', alpha=0.7)
    ax1.plot(np.imag(rx_samples), label='Imag (Q)', color='red', linestyle='--', alpha=0.7)
    ax1.set_title(f"Time Domain: Received Signal ({num_samples} samples)")
    ax1.set_xlabel("Sample Index")
    ax1.set_ylabel("Amplitude")
    ax1.legend()
    ax1.grid(True)
    
    # Frequency Domain Plot
    ax2.plot(freqs / 1e6, mag_db, color='green') # X-axis in MHz
    ax2.set_title("Frequency Domain: Magnitude Spectrum")
    ax2.set_xlabel("Frequency Offset (MHz)")
    ax2.set_ylabel("Magnitude (dB)")
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

# --- RUNNING THE TEST ---
# Ensure your transmitter is running the sinusoid code first!
# receive_and_plot(usrp, num_samples=500*scaling)

receive_and_plot_FFT(usrp, num_samples=500*scaling)