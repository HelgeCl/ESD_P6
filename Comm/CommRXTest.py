from Git.ESD_P6.Comm.SPPEncoder import SPPEncoder
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from Git.ESD_P6.Comm.BPSK import BPSK
from Git.ESD_P6.Comm.SDR import SDR
import numpy as np

decoder = SPPDecoder()

Received_signal = sdr.RX(num_samples=len(Transmitted_signal), channel=(1, ))

Decoded_packet = decoder.decode(Received_signal)

print("Received packet (hex):", Decoded_packet)