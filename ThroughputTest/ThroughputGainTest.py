from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack, recv_data
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from time import sleep, time
import numpy as np

IS_PI1 = (gethostname() == "pi1")

threshold = 5

duration = 30 # seconds



if IS_PI1 is True:
    decoder = SPPDecoder(102)
    id = 101
    radio = RXTX(tx_apid=101, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)
    
else:
    decoder = SPPDecoder(101)
    id = 102
    radio = RXTX(tx_apid=102, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)

case = None
packet_count = 0
timestamp = 0
msg = "gain"
msg_start = ""
test_sync_msg = "start"
max_gain = 85
current_gain = 0
data = []
results = []
gains = []
throughputs = []

def GainSelect():
    global current_gain,radio
    if current_gain < max_gain:
        current_gain += 1
        radio = RXTX(tx_apid=101,gain_tx=current_gain, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)
        radio.transmit(str(current_gain))
    else:
        quit()

def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None  # or a default, or re-raise


while True:
    if IS_PI1: #TX
            GainSelect()
            timeout = time()
            while (time() - timeout) < 10:
                data_start = recv_data(radio, decoder)
                if data_start is None:
                    print("Received none instead of start")
                    radio.transmit(str(current_gain))
                    #continue
                    msg_start = ""
                else:
                    msg_start,idk = data_start
                if msg_start == "start":
                    while True:
                        print("Starting spam")
                        sleep(0.1)  # Ensure Pi2 is in recv mode
                        start_time = time()
                        while (time() - start_time) < duration + 10: # Plus 10 for at undgå de 6 sekunder uden data
                            timestamp = time() - start_time
                            packet_count += 5
                            print(f"Time: {timestamp} packet: {packet_count}")
                            radio.transmit(msg)
                        print("Stopping spam")
                        packet_count = 0
                        break
                elif (time() - timeout) < 9:
                    
                    print(f"No start received at {current_gain} dB, increasing gain")
    else: #RX
        while current_gain < max_gain:
            data_ng = recv_data(radio, decoder)
            if data_ng is None:
                continue
            packet, idk = data_ng
            packet = to_int(packet)
            if packet is None:
                continue
            current_gain = packet
            print(f"Received new gain: {current_gain} dB, starting test")

            # Keep sending "start" until we see data coming back
            start_time = time()
            while (time() - start_time) < duration:
                radio.transmit("start")         # retransmit "start" each loop
                data_res = recv_data(radio, decoder)
                if data_res is None:
                    continue
                result, idk = data_res
                if result == msg:
                    timestamp = time() - start_time
                    data.append(timestamp)
                # once data is flowing, stop sending "start"
                elif result == str(current_gain):
                    continue  # Pi1 still announcing gain, keep sending start
                
