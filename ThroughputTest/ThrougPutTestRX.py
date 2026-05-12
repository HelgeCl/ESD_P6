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
data = []
packet_count = 0

if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102)

case = None

while True:
    if IS_PI1 != True:
            print("Sending start")
            radio.transmit("start")
            start_time = time()
            while (time() - start_time) < duration:
                print(f"Runtime: {time()-start_time}")
                result = recv_data(radio, decoder)
                print(result)
                if  result == "spam":
                    timestamp = time() - start_time
                    packet_count += 1
                    print(f"Time: {timestamp} packet: {packet_count}")
                    data.append([timestamp, packet_count])
            print("Stopping test...")
            break

np.savetxt("results.csv", data, delimiter=",", header="time,packet_count", comments="")
            
                
