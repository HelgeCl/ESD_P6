from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack, recv_data, esprit_correction
from Git.ESD_P6.AoA.DoA import delay_and_sum, esprit
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from time import sleep
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

while True:
    # Trying to detect the other
    if IS_PI1:
        radio.transmit("PI1", random.randint(1, 15))
        data = recv_data(radio, decoder)
        if data is None:
            continue
        msg, esprit_data = data
        if msg == "connection":
            print("Received answer from Pi2, sending ACK")
            angle = run_esprit_and_move(esprit_data)
            print("Angle is: ", angle)
            sleep(0.1)  # Ensure Pi2 is in recv mode
            radio.transmit("ACK:PI1")
            case = "transmit_data"
        if case is not None:
            break

    else:
        data = recv_data(radio, decoder)
        if data is None:
            continue
        msg, esprit_data = data
        print("Detected other station, it doesnt know us yet")
        print("received msg is: ", msg)

        angle = run_esprit_and_move(esprit_data)

        print("Waiting for listing period")
        while data is not None:
            data = recv_data(radio, decoder, timeout = 1)
        
        sleep(0.1)
        print("Transmitting")
        radio.transmit("connection")
        case = "receive_data"

        if check_ack(radio, decoder, "ACK:PI1"):
            print("received ACK")
            break
        else:
            print("Did not receive ACK, checking if Pi1 is in transmit mode")
            if recv_data(radio, decoder) is not None:
                print("ACK didnt reach us, but msg reached Pi1")
                break
            else:
                print("Full retry")


while True:
    match case:
        case "transmit_data":
            #print("Transmitting data")
            if IS_PI1 is True:
                radio.transmit("Some important data")
                sleep(0.1)
                if check_ack(radio, decoder, "ACK:PI2", 1):
                    case = "receive_data"
            else:
                radio.transmit("Some SUPER-important data")
                sleep(0.1)
                ack, msg = check_ack(radio, decoder, "ACK:PI1", 1, output_string=True)
                if ack:
                    case = "receive_data"
                    continue
                if msg is not None: #If we receive a message, previous ack didnt go through.
                    print("Ack didnt go through")
                    radio.transmit("ACK:PI2")

        case "receive_data":
            #print("receiving data")
            data = recv_data(radio, decoder)
            if data is None:
                continue
            msg, esprit_data = data
            if msg:
                if "ACK" in msg:
                    continue  # In this state we should not receive acks
                if IS_PI1 is True:
                    print("From Pi2 the following has been received (sending ACK):")
                    print(msg)
                    data = recv_data(radio, decoder, timeout = 0.5)
                    while data is not None:# Ensure Pi2 is in recv mode
                        data = recv_data(radio, decoder, timeout = 0.5)
                    radio.transmit("ACK:PI1")
                else:
                    print("From Pi1 the following has been received (sending ACK):")
                    print(msg)
                    data = recv_data(radio, decoder, timeout = 0.5)
                    while data is not None:# Ensure Pi1 is in recv mode
                        data = recv_data(radio, decoder, timeout = 0.5)
                    radio.transmit("ACK:PI2")
                angle = run_esprit_and_move(esprit_data)
                print("Angle is: ", angle)
                case = "transmit_data"