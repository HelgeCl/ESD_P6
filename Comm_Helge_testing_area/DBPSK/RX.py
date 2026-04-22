import uhd
import numpy as np

# Parameters
SAMP_PER_BIT = 32 # Resulting bit rate: 1e6 / 32 = 31.25 Kbps
sample_rate = 1e6    # 1 MHz (Lower is more stable for testing)
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


def transmit():
    # 1. Create a Preamble (13-bit Barker code) for synchronization
    barker = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])
    
    # 2. Convert message to bits/symbols
    message = "HELLO BPSK"
    bits = ''.join(format(ord(i), '08b') for i in message)
    data_symbols = np.array([1 if b == '1' else -1 for b in bits])
    
    # Combine and Oversample
    payload = np.concatenate((barker, data_symbols))
    samples = np.repeat(payload, SAMP_PER_BIT).astype(np.complex64)

    print(f"Transmitting...")
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    tx_streamer = usrp.get_tx_stream(st_args)
    
    # Continuous loop transmission
    metadata = uhd.types.TXMetadata()
    try:
        while True:
            tx_streamer.send(samples, metadata)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    transmit()