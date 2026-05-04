import numpy as np
from Comm.TX_RX import RXTX
from Comm.SPPDecoder import SPPDecoder


def check_ack(radio: RXTX, decoder: SPPDecoder, ack_string, timeout: float = 5):
    bits = radio.receive(timeout=timeout)
    for seq in bits:
        decoded_msg = decoder.decode(seq)
        decoded_msg = bytes.fromhex(decoded_msg['data']).decode('ascii', errors='replace')
        if decoded_msg.get('data') == ack_string:
            return True
    return False


def detect_signal(signal, window_size, threshold):
    """
    Performs FFT returns the middle window of three consecutive windows 
    that exceed threshold.
    """
    num_samples = len(signal)
    consecutive_count = 0

    # Iterate through the signal, non-overlapping steps
    i = 0
    while i < num_samples:
        window = signal[i: i + window_size]

        fft_result = np.fft.fft(window, n=8192)

        magnitude = np.abs(fft_result)

        if magnitude > threshold:
            consecutive_count += 1
        else:
            consecutive_count = 0  # Reset if the streak is broken

        if consecutive_count == 3:
            return signal[i - window_size: i]  # Return last window

        i = i+window_size

    return None  # Return None if no trigger occurs
