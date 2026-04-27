from Git.ESD_P6.Comm_Therk.TX_RX import transmit, receive
from Git.ESD_P6.Comm_Therk.SPPEncoder import SPPEncoder
from Git.ESD_P6.Comm_Therk.SPPDecoder import SPPDecoder

if __name__ == "__main__":
    encode= SPPEncoder()
    decode = SPPDecoder(bit_rate=1e6)
    ack_req = False
    while ack_req == False:
        rec_msg = receive()
        if rec_msg is not None:
            decoded_msg = decode.decode(rec_msg)
            print(f"Decoded message: {decoded_msg}")
            ack_req = True
    while ack_req == True:
        enc_msg = encode.encode(
            packet_type=0,        # telecommand
            apid=2, # Predefineret apid
            seq_flag=3,           # 0 for continuation, 1 for first, 2 for last, 3 for sole
            sequence_count=0, # Fortæller hvilket nr. pakket dette er, kun relevant
            data="ACK: Message received successfully!", # Obv. data i dette tilfælde 'message'
            sec_hdr_flag=0 # 0 for ingen sec header, 1 for sec header
        )
        transmit(enc_msg)
        ack_req = False