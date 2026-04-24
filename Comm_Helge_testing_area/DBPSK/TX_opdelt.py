from Git.ESD_P6.SDR_class import SDR
import numpy as np

# Parameters
SAMP_PER_BIT = 32 # Resulting bit rate: 1e6 / 32 = 31.25 Kbps
sample_rate = 1e6
center_freq = 5.8e9
gain = 60

sdr = SDR(sample_rate, center_freq, gain, gain, [0])
sdr.setup_transmit()

def transmit(sdr: SDR, message):
    # 1. Create a Preamble (13-bit Barker code) for synchronization
    barker = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])

    # 2. Convert message to bits/symbols
    message = str(message)
    bits = ''.join(format(ord(i), '08b') for i in message)
    data_symbols = np.array([1 if b == '1' else -1 for b in bits])

    # Combine and Oversample
    payload = np.concatenate((barker, data_symbols))
    samples = np.repeat(payload, SAMP_PER_BIT).astype(np.complex64)

    #print(f"Transmitting...")
    sdr.transmit(samples)
    


if __name__ == "__main__":
    i=0
    while True:
        i=i+1
        transmit(sdr, str(i))
