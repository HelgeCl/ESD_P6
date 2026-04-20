import uhd
import numpy as np

RX_GAIN = 60
TX_GAIN = 60
channels = [0, 1]
sample_rate = 30e6
center_freq = 5.8e9


usrp = uhd.usrp.MultiUSRP()
#usrp.set_master_clock_rate(32e6)


for chan in channels:
    usrp.set_rx_antenna('TX/RX', chan)
    usrp.set_rx_gain(RX_GAIN, chan)
    usrp.set_rx_rate(sample_rate, chan)
    usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)

    usrp.set_tx_gain(TX_GAIN, chan)
    usrp.set_tx_rate(sample_rate, chan)
    usrp.set_tx_freq(uhd.libpyuhd.types.tune_request(center_freq), chan)




# Alt herunder er AI
def transmit_dbpsk_robust(usrp, data_bits, sps=16):
    # 1. Differential Encoding
    dbpsk_bits = np.ones(len(data_bits) + 1)
    curr = 1
    for i, b in enumerate(data_bits):
        if b == 0: curr *= -1
        dbpsk_bits[i+1] = curr

    # 2. Pulse Shaping (Square pulse for simplicity, but oversampled)
    # This repeats each bit 'sps' times
    symbols = np.repeat(dbpsk_bits, sps).astype(np.complex64)

    # 3. Transmit
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    streamer = usrp.get_tx_stream(st_args)
    metadata = uhd.types.TXMetadata()
    streamer.send(symbols, metadata)
    return len(symbols)

def receive_dbpsk_robust(usrp, num_bits, sps=16):
    # Capture more samples than needed to ensure the message is inside the buffer
    num_samples = (num_bits + 50) * sps
    
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    streamer = usrp.get_rx_stream(st_args)
    buffer = np.zeros((1, num_samples), dtype=np.complex64)
    metadata = uhd.types.RXMetadata()
    
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.num_done)
    stream_cmd.num_samps = num_samples
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)
    streamer.recv(buffer, metadata)
    
    rx_sig = buffer[0]

    # 1. Differential Detection
    # Multiply signal by a delayed version of itself
    # We delay by 'sps' because that's the distance between bit centers
    diff_prod = rx_sig[sps:] * np.conj(rx_sig[:-sps])

    # 2. Magnitude Check (Is there actually a signal?)
    # If the average magnitude is very low, you're just seeing noise
    if np.mean(np.abs(diff_prod)) < 1e-4:
        print("Warning: Signal level very low. Check gains/antenna.")

    # 3. Simple Clock Recovery (The 'Best Offset' trick)
    # We try every possible offset within one symbol to find the strongest real part
    best_offset = 0
    max_val = 0
    for i in range(sps):
        test_sum = np.sum(np.abs(np.real(diff_prod[i::sps])))
        if test_sum > max_val:
            max_val = test_sum
            best_offset = i

    # 4. Slice the bits
    recovered_bits = (np.real(diff_prod[best_offset::sps]) > 0).astype(int)
    
    # Trim to expected length
    return recovered_bits[:num_bits]


## Normalt igen

pattern = np.array([0, 0, 1, 1, 0, 1], dtype=np.int32)
tx_bits = np.tile(pattern, 2500000) # 10,000 bits
tx_bits = np.repeat(tx_bits, 1)

# 3. Convert to BPSK Symbols
symbols = np.where(tx_bits == 1, 1.0 + 0j, -1.0 + 0j).astype(np.complex64)

while True:
    transmit_dbpsk_robust(usrp, tx_bits)


"""
Receive:
print(receive_dbpsk_robust(usrp,100))

"""