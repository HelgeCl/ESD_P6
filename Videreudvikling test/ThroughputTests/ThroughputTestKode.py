from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
import random
from Git.ESD_P6.Collected_solution.misc import detect_signal, check_ack, recv_data
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from time import sleep, time
import numpy as np
from lblprof import start_tracing, stop_tracing, show_interactive_tree, show_tree

##########################################
#Start pi1 foerst
##########################################


IS_PI1 = (gethostname() == "pi1")

threshold = 5
test_num = 0 #Current test
num_test = 30 #Number of tests to run
duration = 60 # seconds
test_data = []
lost_data = []
test_results = np.empty((0,3))
lost_packet_count = 0
prev_packet = int(0)
timestamp = 0

if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102)




def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None  # or a default, or re-raise



if IS_PI1: #TX
    print("Waiting for start command")
    while True:
        data = recv_data(radio, decoder) 
        if data is None:
            #print("No work")
            continue
        packet,esprit = data
        if packet == "start":
            print(f"Starting spam: {test_num}")
            sleep(0.1)  # Ensure Pi2 is in recv mode
            start_time = time()
            while (time() - start_time) < duration:
                timestamp = time() - start_time
                packet_count += 1
                #print(f"Time: {timestamp} packet: {packet_count}")
                #start_tracing()
                radio.transmit(str(packet_count),repeat = 2)
                #stop_tracing()
                #show_tree() # print the tree to console
            print(f"Time: {timestamp} packets: {packet_count}")
            print(f"Stopping test: {test_num}")
            test_num += 1
            packet_count = 0
else: #RX
    for i in range(num_test):
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
                if packet_int is None or packet_int < prev_packet: #Frasortere duplicates og aeldre pakker
                    continue
                else:
                    test_data.append([timestamp, packet_int])
                    prev_packet = packet_int
            else:
                continue
            
            
        print(f"Stopping test {i}...")
        #Gemmer data saa man kan se, hvis der er noget maerkligt i resultaterne
        np.savetxt(f"packets_grpNoRepeatNyTestNoStop{i}.csv", test_data, delimiter=",", header="time,packet_count", comments="")

        if len(test_data) == 0:
            print(f"No data received in test {i}, skipping...")
            sleep(5) #Lille delay for at sikre Pi1 er klar til at modtage ny 'start'
            continue 
        
        np_test_data = np.array(test_data).reshape(-1,2)
        packet_per_sec = len(test_data)/max(np_test_data[:,0])
        max_bit_per_sec = packet_per_sec * 256 #256 da dette er den laengste besked vi kan sende
        packet_error_rate = 1-(len(test_data)/6020) #TX sender 6020 pakker hver gang

        test_results = np.vstack([test_results, [packet_per_sec, max_bit_per_sec, packet_error_rate]])

        test_data = []
        lost_data = []
        lost_packet_count = 0
        sleep(5) #Lille delay for at sikre Pi1 er klar til at modtage ny 'start'

    #Udregner resultat
    packet_per_sec_mean = np.mean(test_results[:,0])
    max_bit_per_sec_mean = np.mean(test_results[:,1])
    packet_error_rate_mean = np.mean(test_results[:,2])
    print(f"Average packet per second: {packet_per_sec_mean}")
    print(f"Average max bit per second: {max_bit_per_sec_mean}")
    print(f"Average packet error rate: {packet_error_rate_mean}")
            
