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
    radio = RXTX(tx_apid=102,gain_rx=10, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)

case = None
packet_count = 0
timestamp = 0
msg = "gain"
test_sync_msg = "start"
max_gain = 85
current_gain = 43
data = []
results = []
gains = []
throughputs = []

def GainSelect():
    global current_gain
    if current_gain < max_gain:
        current_gain += 3
        radio = RXTX(tx_apid=101,gain_tx=current_gain)
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
                    continue
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
                print("None at new gain")
                continue
            packet,idk = data_ng
            packet = to_int(packet)
            print(packet)
            current_gain = packet
            print(f"Received new gain: {current_gain} dB, starting test")
            print("Sending start")
            radio.transmit("start")
            print("Starting...")
            start_time = time()
            while (time() - start_time) < duration:
                #sleep(8) # Fjerner de 6 sek, hvor der ikke kom data
                data_res = recv_data(radio, decoder)
                if data_res is None:
                    print("Is none at results")
                    continue
                result ,idk = data_res
                print(result)
                if  result == msg:
                    timestamp = time() - start_time
                    print(f"Time: {timestamp} packet: {len(data)}")
                    data.append(timestamp)
            print(f"Stopping current test...")
            packet_count = 0
            throughput = (len(data) * (6 + len(msg)) * 8) / max(data)
            results.append([current_gain, throughput])
            data = []                #results.append([current_gain,data,])
        print("Test ended")
        np.savetxt(f"results_gainSweepLowRXGain.csv", results, delimiter=",", header="gain,throughput", comments="")
        break
                
