import numpy as np
import uhd
import time

# --- Configuration ---
sample_rate = 30e6    # 1 MHz (Lower is more stable for testing)
center_freq = 5.8e9  # 2.4 GHz (Try this if 5.8 GHz was weak)
tone_freq = 10e3     # 10 kHz (The frequency of the actual beep/tone)
gain = 60            # High gain for B200 antennas
channels = [0]

# --- USRP Setup ---
usrp = uhd.usrp.MultiUSRP()

for chan in channels:
    usrp.set_rx_gain(gain, chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

    usrp.set_tx_gain(gain, chan)
    usrp.set_tx_rate(sample_rate, chan)
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)


# --- Generate Sine Wave ---
# Create 1 second worth of samples
t = np.arange(0, 1.0, 1.0/sample_rate)
# We multiply by 0.5 to stay below the digital clipping limit (1.0)
sine_wave = (0.5 * np.exp(2j * np.pi * tone_freq * t)).astype(np.complex64)

# --- Streaming ---
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = channels
streamer = usrp.get_tx_stream(st_args)
metadata = uhd.types.TXMetadata()

print(f"Transmitting {tone_freq/1000} kHz tone at {center_freq/1e9} GHz...")

try:
    while True:
        # Continuously pump the sine wave buffer to the hardware
        streamer.send(sine_wave, metadata)
except KeyboardInterrupt:
    print("\nStopping transmission.")