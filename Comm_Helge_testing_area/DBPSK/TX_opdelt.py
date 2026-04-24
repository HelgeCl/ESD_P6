from Git.ESD_P6.SDR_class import SDR
import numpy as np

# Parameters
SAMPLES_PR_BIT = 32  # Resulting bit rate: 1e6 / 32 = 31.25 Kbps
SAMPLE_RATE = 1e6
CENTER_FREQ = 5.8e9
GAIN_RX = 60
GAIN_TX = 60

sdr = SDR(SAMPLE_RATE, CENTER_FREQ, GAIN_RX, GAIN_TX, [0])
sdr.setup_transmit()


def transmit(sdr: SDR, msg):
    # barker code:
    barker = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])

    msg = str(msg)  # Ensures msg is string

    msg_as_bytes = np.frombuffer(msg.encode('utf-8'), dtype=np.uint8)  # String to bytes
    bits = np.unpackbits(msg_as_bytes)  # From e.g. 70 to bits e.g. [0, 1, 0, 0, ...]
    data_symbols = (bits.astype(np.float32) * 2) - 1  # from bits to +-1:
    # (1 * 2) - 1 = 1
    # (0 * 2) - 1 = -1
    # Float32 to ensure samples is in correct datatype complex 64 for the SDR

    # Combine and insert more samples pr. bit
    payload = np.concatenate((barker, data_symbols))
    samples = np.repeat(payload, SAMPLES_PR_BIT).astype(np.complex64)

    sdr.transmit(samples)


if __name__ == "__main__":
    i = 0
    while True:
        i = i+1
        transmit(sdr, str(i))
