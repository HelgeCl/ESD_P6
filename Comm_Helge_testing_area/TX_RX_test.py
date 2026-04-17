import uhd
import numpy as np

RX_GAIN = 10
TX_GAIN = 10
channels = [0, 1]
sample_rate = 30e6
center_freq = 5.8e9


usrp = uhd.usrp.MultiUSRP()


for chan in channels:
    usrp.set_rx_antenna('RX1', chan)
    usrp.set_rx_gain(RX_GAIN, chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

    usrp.set_tx_gain(TX_GAIN, chan)
    usrp.set_tx_rate(sample_rate, chan)
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)


# Alt herunder er AI

def transmit_bpsk(usrp, data_bits, tx_rate, tx_channels=[0]):
    """
    Converts bits to BPSK symbols and streams them via USRP.
    """
    # 1. Modulation: Map 0 -> -1, 1 -> 1
    # We use complex64 because USRPs expect IQ pairs
    symbols = np.where(data_bits == 1, 1.0 + 0j, -1.0 + 0j).astype(np.complex64)

    # 2. Setup Streamer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = tx_channels
    streamer = usrp.get_tx_stream(st_args)

    # 3. Transmit
    metadata = uhd.types.TXMetadata()
    # Sending the buffer
    num_sent = streamer.send(symbols, metadata)

    print(f"Sent {num_sent} BPSK symbols.")
    return num_sent


def receive_bpsk(usrp, num_samples, rx_channels=[0]):
    """
    Receives samples from USRP and demodulates BPSK.
    """
    # 1. Setup Streamer
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    st_args.channels = rx_channels
    streamer = usrp.get_rx_stream(st_args)

    # 2. Receive Samples
    buffer = np.zeros((len(rx_channels), num_samples), dtype=np.complex64)
    metadata = uhd.types.RXMetadata()

    # Start streaming
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd.num_samps = num_samples
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    streamer.recv(buffer, metadata)

    # 3. Demodulation: BPSK Decision Logic
    # If the Real part is > 0, it's a 1. Otherwise, it's a 0.
    received_samples = buffer[0]  # Taking the first channel
    recovered_bits = (np.real(received_samples) > 0).astype(int)

    return recovered_bits, received_samples
