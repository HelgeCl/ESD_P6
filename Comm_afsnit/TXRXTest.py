from Git.ESD_P6.Comm.SPPEncoder import SPPEncoder
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from Git.ESD_P6.Comm.BPSK import BPSK
from Git.ESD_P6.Comm.SDR import SDR
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

# Convert the bytes object into a NumPy array of uint8
byte_array = np.frombuffer(encoded_packet, dtype=np.uint8)

# Unpack the bits into a flat array of 0s and 1s
bits = np.unpackbits(byte_array)
print("Packet without secondary header (hex):", encoded_packet.hex())

bpsk = BPSK(fs=20e6, fc=5.8e9, num_symbols=100)

sdr = SDR(master_clock_rate=40e6, tx_gain=40, rx_gain=20)

encoded_packet_bits = np.unpackbits(np.frombuffer(encoded_packet, dtype=np.uint8))

#modulated_signal = bpsk.modulate(bits = encoded_packet_bits)

print("Encoded packet:", bits)

Transmitted_signal = sdr.TX(encoded_packet=encoded_packet_bits, channel=0)

print("Transmitted packet:", Transmitted_signal)

demodded_signal = bpsk.demodulate(Transmitted_signal)

print("Demodded packet:", demodded_signal)

decoded_signal = decoder.decode(demodded_signal)

print("Decoded packet:", decoded_signal)