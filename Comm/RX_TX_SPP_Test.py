import threading
import queue
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Comm.SPPEncoder import SPPEncoder
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder

cmd_queue = queue.Queue()


def listen_for_commands():
    while True:
        cmd = input()
        cmd_queue.put(cmd)


if __name__ == "__main__":
    encode = SPPEncoder()
    decode = SPPDecoder(bit_rate=1e6)

    radio = RXTX()
    allow_rec = True

    thread = threading.Thread(target=listen_for_commands, daemon=True)
    thread.start()

    while True:
        # --- Handle keyboard commands first ---
        try:
            cmd = cmd_queue.get_nowait()
            if cmd == "quit":
                print("Quitting...")
                break
            elif cmd == "ping adversary":
                print("Pinging adversary")
                radio.transmit("REQ:ACTIVE?")
                # FIX: After transmitting, immediately drop into receive to catch the ACK.
                # The old code went around the main loop first, burning time while the
                # peer was already listening and counting down its receive timeout.
                allow_rec = True
            elif cmd == "stop rec":
                allow_rec = False
            elif cmd == "start rec":
                print("Listening...")
                allow_rec = True
        except queue.Empty:
            pass

        # --- Receive loop ---
        if allow_rec:
            # FIX: Pass a meaningful timeout so receive() doesn't give up after 200ms.
            # 5 seconds gives ample time for the peer to switch modes and transmit.
            rec_bits = radio.receive(timeout=5.0)

            if rec_bits is None:
                # Timed out — nothing received, loop back and check commands again
                continue

            decoded_msg = decode.decode(rec_bits)
            if decoded_msg is None:
                print("Received undecodable packet, ignoring")
                continue

            print(
                f"Decoded message: {decoded_msg | {'data': bytes.fromhex(decoded_msg['data']).decode('ascii', errors='replace')}}")

            # FIX: Respond immediately in the same iteration, not on the next loop.
            # Previously ack_req was set True and the ACK was sent one full loop
            # iteration later — by then the peer had often already timed out.
            if decoded_msg.get('data') == '5245513a4143544956453f':
                print("Received REQ:ACTIVE? — sending ACK immediately")
                radio.transmit("ACK:PI1HERE!")
            # else:
                # print("Unknown message received, stopping receive")
