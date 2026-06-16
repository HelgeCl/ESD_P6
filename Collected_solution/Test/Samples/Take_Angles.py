from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Collected_solution.misc import recv_data, esprit_correction
from Git.ESD_P6.AoA.DoA import esprit
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from Git.ESD_P6.ControllerCommunication.ControllerCom import deg2step, makeCommandData
from Git.ESD_P6.ControllerCommunication.SerialRW import serial_write
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

def run_esprit_and_move(esprit_data):
    corrected_data = esprit_correction(esprit_data)
    angle = -esprit(corrected_data, 1)
    serial_write(stepper, makeCommandData(deg2step(angle)))
    return angle

ang = "-60"

angles = []
while True:
    data = recv_data(radio, decoder)
    if data is None:
        continue
    msg, esprit_data = data
    angle = run_esprit_and_move(esprit_data)
    angles.append(angle)
    if len(angles)>=500:
        np.savez_compressed('angles_degree_'+ang+'.npz', angles=angles)
        sampes = radio.sample_and_rtn(10e6)
        np.savez_compressed('data_from_degree_'+ang+'.npz', RX0=sampes[0], RX1=sampes[1])

        exit()
