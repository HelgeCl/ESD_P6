from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack, recv_data
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from time import sleep, time
import numpy as np
from lblprof import start_tracing, stop_tracing, show_interactive_tree, show_tree

IS_PI1 = (gethostname() == "pi1")

threshold = 5

duration = 60 # seconds



if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102)

case = None
packet_count = 0
timestamp = 0
print("Waiting for start command")
while True:
    if IS_PI1:
            if recv_data(radio, decoder) == "start":
                while True:
                    print("Starting spam")
                    sleep(0.1)  # Ensure Pi2 is in recv mode
                    start_time = time()
                    while (time() - start_time) < duration:
                        timestamp = time() - start_time
                        packet_count += 1
                        print(f"Time: {timestamp} packet: {packet_count}")
                        #start_tracing()
                        radio.transmit(str(packet_count),repeat=1)
                        #stop_tracing()
                        #show_tree() # print the tree to console
                    print("Stopping spam")
                    packet_count = 0
                
