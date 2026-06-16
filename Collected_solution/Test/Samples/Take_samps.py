from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from serial import Serial
import numpy as np

IS_PI1 = (gethostname() == "pi1")
stepper = Serial("/dev/ttyUSB0", baudrate=115200)

threshold = 5

if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)

case = None

if IS_PI1:
    sampes = radio.sample_and_rtn(10e6)
    np.savez_compressed('data_from_degree_0_gain_35.npz', RX0=sampes[0], RX1=sampes[1])
else:
    while True:
        radio.transmit("Hello")

