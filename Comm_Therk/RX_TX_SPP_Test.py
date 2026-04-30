import threading
import queue
from Git.ESD_P6.Comm_Therk.TX_RX import RXTX
from Git.ESD_P6.Comm_Therk.TX import transmit
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
                radio.transmit("REQ:ACTIVE?")
                
                #transmit("REQ:ACTIVE?")
                #ack_req = True
        except queue.Empty:
            pass

        if ack_req == True:
            print(f"Responding...")  
            radio.transmit("ACK:PI1HERE!")
            
            #transmit("ACK:PI1HERE!")
            ack_req = False
        else:
            print(f"Listening...")
            while ack_req == False and cmd_queue.empty():
                if cmd_queue.empty(): 
                    rec_msg = radio.receive()
                    #print(f"Received data: {rec_msg}")
                    if rec_msg is not None:
                        decoded_msg = decode.decode(rec_msg)
                        if decoded_msg is not None and decoded_msg['data'] == '5245513a4143544956453f':
                            print(f"Decoded message: {decoded_msg}")
                            print("Sending acknowledgement")
                            ack_req = True
                        elif decoded_msg is not None:
                            print(f"Decoded message: {decoded_msg}")
                else:
                     break
        