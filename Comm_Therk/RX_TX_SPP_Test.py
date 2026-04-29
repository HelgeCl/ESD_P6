import threading
import queue
from Git.ESD_P6.Comm_Therk.TX_RX import RXTX
from Git.ESD_P6.Comm_Therk.SPPEncoder import SPPEncoder
from Git.ESD_P6.Comm_Therk.SPPDecoder import SPPDecoder

cmd_queue = queue.Queue()

def listen_for_commands():
    while True:
        cmd = input()
        cmd_queue.put(cmd)

if __name__ == "__main__":
    encode= SPPEncoder()
    decode = SPPDecoder(bit_rate=1e6)
    
    radio = RXTX()
    ack_req = False
    thread = threading.Thread(target=listen_for_commands, daemon=True)
    thread.start()

    while True:
        try:
            cmd = cmd_queue.get_nowait()
            if cmd == "quit":
                print("Quitting...")
                break
            elif cmd == "ping adversary":
                print(f"Pinging adversary")
                enc_msg = encode.encode(
                packet_type=0,        # telecommand
                apid=1, # Predefineret apid
                seq_flag=3,           # 0 for continuation, 1 for first, 2 for last, 3 for sole
                sequence_count=0, # Fortæller hvilket nr. pakket dette er, kun relevant
                data="REQ:ACTIVE?", # Obv. data i dette tilfælde 'message'
                sec_hdr_flag=0 # 0 for ingen sec header, 1 for sec header
                )
                radio.transmit(enc_msg)
                #ack_req = True
        except queue.Empty:
            pass

        if ack_req == True:
            print(f"Responding...")
            enc_msg = encode.encode(
                packet_type=0,        # telecommand
                apid=1, # Predefineret apid
                seq_flag=3,           # 0 for continuation, 1 for first, 2 for last, 3 for sole
                sequence_count=0, # Fortæller hvilket nr. pakket dette er, kun relevant
                data="ACK:PI1HERE!", # Obv. data i dette tilfælde 'message'
                sec_hdr_flag=0 # 0 for ingen sec header, 1 for sec header
            )
            radio.transmit(enc_msg)
            ack_req = False
        else:
            print(f"Listening...")
            while ack_req == False and cmd_queue.empty():
                if cmd_queue.empty(): 
                    rec_msg = radio.receive()
                    #print(f"Received data: {rec_msg}")
                    if rec_msg is not None:
                        decoded_msg = decode.decode(rec_msg)
                        print(f"Decoded message: {decoded_msg}")
                else:
                     break
        