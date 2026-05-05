from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack
from Git.ESD_P6.AoA.DoA import delay_and_sum
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder


IS_PI1 = (gethostname() == "pi1")

threshold = 50

if IS_PI1 is True:
    decoder = SPPDecoder(102, 1e6)
    radio = RXTX(tx_apid=101)
else:
    decoder = SPPDecoder(101, 1e6)
    radio = RXTX(tx_apid=102)


while True:
    # Trying to detect the other
    if IS_PI1:
        radio.transmit_pure_sine(20000+random.randint(1000, 15000))
        bits = radio.receive(timeout=1)
        if bits is not None:
            decoded_msg = decoder.decode(bits)
            if decoded_msg is not None:
                decoded_msg = bytes.fromhex(decoded_msg['data']).decode('ascii', errors='replace')
                if decoded_msg.get('data') == "connection":
                    print("Received answer from Pi2, sending ACK")
                    radio.transmit("ACK:PI1")
                    case = "transmit_data"
                    break

    else:
        sig = radio.sample_and_rtn(20000)
        sig = detect_signal(sig, 2000, threshold)

        if sig is not None:
            print("Detected other station, it doesnt know us yet")
            angle = delay_and_sum(sig, 0.5, 1000)
            print("Angle is: ", angle)
            radio.transmit("connection")
            case = "receive_data"

            if check_ack(radio, decoder, "ACK:PI1"):
                print("received ACK")
                break
            else:
                print("Did not receive ACK, however dont care")
                break


while True:
    match case:
        case "transmit_data":
            if IS_PI1 is True:
                radio.transmit("Some important data")
                if check_ack(radio, decoder, "ACK:PI2"):
                    case = "transmit_carrier"
            else:
                radio.transmit("Some SUPER-important data")
                if check_ack(radio, decoder, "ACK:PI1"):
                    case = "transmit_carrier"

        case "transmit_carrier":
            # NB TEKNISK set er der en chace for at begge er i reciveing data
            radio.transmit_pure_sine(40000)
            case = "receive_data"

        case "receive_data":
            bits = radio.receive()
            if bits is not None:
                decoded_msg = decoder.decode(bits)
                if decoded_msg is not None:
                    decoded_msg = bytes.fromhex(decoded_msg['data']).decode('ascii', errors='replace')
                    if decoded_msg.get('data') != "":
                        if IS_PI1 is True:
                            print("From Pi2 the following has been received (sending ACK):")
                            print(decoded_msg.get('data'))
                            radio.transmit("ACK:PI1")
                        else:
                            print("From Pi1 the following has been received (sending ACK):")
                            print(decoded_msg.get('data'))
                            radio.transmit("ACK:PI2")
                        case = "AoA"

        case "AoA":
            sig = radio.sample_and_rtn(20000)
            sig = detect_signal(sig, 2000, threshold)
            if sig is not None:
                angle = delay_and_sum(sig, 0.5, 1000)
                print("Angle to move is ", angle)
                case = "transmit_data"
            else:
                case = "receive_data"  # It seems we have missed our previous ACK
