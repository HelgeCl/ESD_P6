import numpy as np
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder


def recv_data(radio: RXTX, decoder: SPPDecoder, timeout: float = 5):
    "Only returns a single message"
    data = radio.receive(timeout=timeout)
    if data is not None:
        stream, esprit_data = data
        for package in stream:
            decoded_msg = decoder.decode(package)
            if decoded_msg is not None:
                decoded_msg = bytes.fromhex(decoded_msg['data']).decode('ascii', errors='replace')
                if decoded_msg != "":
                    return decoded_msg, esprit_data


def check_ack(radio: RXTX, decoder: SPPDecoder, ack_string, timeout: float = 5):
    """Checks for a specific acknowlegement string"""
    data = recv_data(radio, decoder, timeout)
    if data is None:
        return False
    msg, _ = data
    if msg == ack_string:
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
        window = signal[0][i: i + window_size]
        fft_result = np.fft.fft(window, n=8192)  # NB fft is technically larger than
        # input data. Is zero padded

        magnitude = np.abs(fft_result)
        max_val = np.max(magnitude)
        mean_val = np.mean(magnitude)
        diff = max_val - mean_val  # If large difference, then its a signal and not noise

        if diff > threshold:
            consecutive_count += 1
        else:
            consecutive_count = 0  # Reset if the streak is broken

        if consecutive_count == 3:
            return signal[:, i - window_size: i]  # Return last window

        i = i+window_size

    return None  # Return None if no trigger occurs


def esprit_correction(esprit_data):
    #sig_cfo = sig * np.exp(-1j * 2 * np.pi * cfo * t)
    #sig_cfo_phase = sig_cfo * np.exp(-1j * phase_offset)
    sig, cfo, phase_offset = esprit_data
    num_samples = sig.shape[1] 
    t = np.arange(num_samples)
    return sig * np.exp(-1j * (2 * np.pi * cfo * t + phase_offset))