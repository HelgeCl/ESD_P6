from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack, recv_data
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from time import sleep, time
import numpy as np

IS_PI1 = (gethostname() == "pi1")

threshold = 5

duration = 60 # seconds



if IS_PI1 is True:
    decoder = SPPDecoder(102)
    id = 101
    
else:
    decoder = SPPDecoder(101)
    id = 102
    radio = RXTX(tx_apid=102)

case = None
packet_count = 0
timestamp = 0
msg = "Testing gain!"
test_sync_msg = "start"
max_gain = 85
current_gain = 0
data = []
lost_data = []


def GainSelect():
    if current_gain < max_gain:
        current_gain += 5
        radio = RXTX(tx_apid=101,gain_tx=current_gain)
        radio.transmit("New Gain")
    else:
        quit()

print("Waiting for start command")
while True:
    if IS_PI1: #TX
            GainSelect()
            timeout = time()
            if time() - timeout < 5:
                if recv_data(radio, decoder) == "start":
                    while True:
                        print("Starting spam")
                        sleep(0.1)  # Ensure Pi2 is in recv mode
                        start_time = time()
                        while (time() - start_time) < duration:
                            timestamp = time() - start_time
                            packet_count += 5
                            print(f"Time: {timestamp} packet: {packet_count}")
                            radio.transmit(msg)
                        print("Stopping spam")
                        packet_count = 0
                else:
                    print(f"Now start received at {current_gain} dB, increasing gain")
    else: #RX
        print("Sending start")
        if recv_data(radio, decoder) == "New Gain":
            radio.transmit("start")
            for i in range(3):
                print("Starting...")
                start_time = time()
                while (time() - start_time) < duration:
                    print(f"Runtime: {time()-start_time}")
                    result = recv_data(radio, decoder)
                    print(result)
                    if  result == msg:
                        timestamp = time() - start_time
                        packet_count += 1
                        print(f"Time: {timestamp} packet: {len(data)}")
                        data.append(timestamp)
                    else:
                        timestamp = time() - start_time
                        lost_packet_count += 1
                        print(f"Time: {timestamp} lost_packet: {len(lost_data)}")
                        lost_data.append(timestamp)
                print(f"Stopping test {i}...")
                np.savetxt(f"results_grp60g{i}.csv", data, delimiter=",", header="time,packet_count", comments="")
                np.savetxt(f"lost_results_grp60g{i}.csv", lost_data, delimiter=",", header="time,packet_count", comments="")
                packet_count = 0
                lost_packet_count = 0
                
