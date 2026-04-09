from SPPEncoder import SPPEncoder
from SPPDecoder import SPPDecoder
from BPSK import BPSK
from SDR import SDR
import numpy as np

encoder = SPPEncoder(version=0)  # CCSDS version 0
decoder = SPPDecoder()

encoded_packet = encoder.encode(
        packet_type=0,        # telecommand
        apid=123,
        seq_flag=3,           # sole packet
        sequence_count=0,
        data=b'Fat ass monkey!',
        sec_hdr_flag=0
    )
print("Packet without secondary header (hex):", encoded_packet.hex())

bpsk = BPSK(fs=1e6, fc=100e3, num_symbols=100)

sdr = SDR(master_clock_rate=60e6, tx_gain=10, rx_gain=20)

encoded_packet_bits = np.unpackbits(np.frombuffer(encoded_packet, dtype=np.uint8))

#modulated_signal = bpsk.modulate(bits = encoded_packet_bits)

Transmitted_signal = sdr.TX(encoded_packet=encoded_packet, channel=0)

print("Transmitted packet:", Transmitted_signal)

Received_signal = sdr.RX(num_samples=len(Transmitted_signal), channel=(1, ))

Decoded_packet = decoder.decode(Received_signal)

print("Received packet (hex):", Decoded_packet)