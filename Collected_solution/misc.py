import numpy as np
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder


def check_ack(radio: RXTX, decoder: SPPDecoder, ack_string, timeout: float = 5):
    bits = radio.receive(timeout=timeout)
    if bits is not None:
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
    num_samples = len(signal[0])
    consecutive_count = 0

    # Iterate through the signal, non-overlapping steps
    i = 0
    while i < num_samples:
        print("i: ", i)
        window = signal[0][i: i + window_size]

        fft_result = np.fft.fft(window, n=8192)

        magnitude = np.abs(fft_result)
        max_val = np.max(magnitude)
        mean_val = np.mean(magnitude)
        diff = max_val - mean_val
        print("diff is: ", diff)

        if diff > threshold:
            consecutive_count += 1
            print("cont_cont ", consecutive_count)
        else:
            consecutive_count = 0  # Reset if the streak is broken

        if consecutive_count == 3:
            return signal[:,i - window_size: i]  # Return last window

        i = i+window_size

    return None  # Return None if no trigger occurs
