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
test_data = []
lost_data = []
test_results = np.empty((0,3))
#packet_count = 0
lost_packet_count = 0
prev_packet = int(0)

if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102,gain_rx=60, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)

case = None

def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None  # or a default, or re-raise

if IS_PI1 != True:
    for i in range(31):
        print("Sending start")
        radio.transmit("start")
        print("Starting...")
        start_time = time()
        while (time() - start_time) < duration:
            #print(f"Runtime: {time()-start_time}")
            #start_tracing()
            data = recv_data(radio, decoder)
            #stop_tracing()
            #show_tree() # print the tree to console
            if data is None:
                #print("No work")
                continue
            packet,esprit = data
            #print(packet)
            if  packet is not None:
                timestamp = time() - start_time
                #print(f"Time: {timestamp} packet: {packet}")
                packet_int = to_int(packet)
                if packet_int is None or packet_int < prev_packet:
                    lost_packet_count += 1
                    #print(f"Time: {timestamp} lost_packet: {lost_packet_count}")
                    lost_data.append([timestamp, lost_packet_count])
                else:
                    test_data.append([timestamp, packet_int])
                    prev_packet = packet_int
            else:
                timestamp = time() - start_time
                lost_packet_count += 1
                #print(f"Time: {timestamp} lost_packet: {lost_packet_count}")
                lost_data.append([timestamp, lost_packet_count])
            
            
        print(f"Stopping test {i}...")

        np.savetxt(f"packets_grpNoRepeatNyTestNoStop{i}.csv", test_data, delimiter=",", header="time,packet_count", comments="")
        #np.savetxt(f"lost_packets_grpNoRepeatNyTestNoStop{i}.csv", lost_data, delimiter=",", header="time,packet_count", comments="")

        if len(test_data) == 0:
            print(f"No data received in test {i}, skipping...")
            sleep(5)
            continue
        np_test_data = np.array(test_data).reshape(-1,2)
        packet_per_sec = len(test_data)/max(np_test_data[:,0])
        max_bit_per_sec = packet_per_sec * 256
        packet_error_rate = 1-(len(test_data)/6020)

        test_results = np.vstack([test_results, [packet_per_sec, max_bit_per_sec, packet_error_rate]])

        
        test_data = []
        lost_data = []
        lost_packet_count = 0
        sleep(5)
    packet_per_sec_mean = np.mean(test_results[:,0])
    max_bit_per_sec_mean = np.mean(test_results[:,1])
    packet_error_rate_mean = np.mean(test_results[:,2])
    print(f"Average packet per second: {packet_per_sec_mean}")
    print(f"Average max bit per second: {max_bit_per_sec_mean}")
    print(f"Average packet error rate: {packet_error_rate_mean}")


            
                
