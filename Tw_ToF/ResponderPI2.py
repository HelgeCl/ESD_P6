import uhd
import numpy as np
import time
from scipy.signal import correlate

def generate_zc_sequence(N=127, u=29):
    n = np.arange(N)
    return np.exp(-1j * np.pi * u * n * (n + 1) / N).astype(np.complex64)

def setup_responder():
    usrp = uhd.usrp.MultiUSRP("type=b200")
    usrp.set_master_clock_rate(32e6)
    usrp.set_rx_rate(10e6)
    usrp.set_tx_rate(10e6)
    usrp.set_tx_gain(0, 0)      # Safety for patch antennas
    usrp.set_rx_gain(30, 0)
    usrp.set_time_now(uhd.types.TimeSpec(0.0))
    return usrp

def run_responder(usrp, ref_signal, fixed_delay_s=0.01):
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    rx_streamer = usrp.get_rx_stream(st_args)
    tx_streamer = usrp.get_tx_stream(st_args)
    
    rx_buffer = np.zeros(20000, dtype=np.complex64)
    rx_md = uhd.types.RXMetadata()

    print("Responder: Listening for Poll...")
    while True:
        num_rx = rx_streamer.recv(rx_buffer, rx_md)
        if num_rx > 0 and rx_md.has_time_spec:
            corr = correlate(rx_buffer, ref_signal, mode='valid')
            mag_corr = np.abs(corr)
            peak_idx = np.argmax(mag_corr)
            
            if mag_corr[peak_idx] > 10.0:
                t2_peak = rx_md.time_spec.get_real_secs() + (peak_idx / usrp.get_rx_rate())
                t3 = uhd.types.TimeSpec(t2_peak + fixed_delay_s)
                
                tx_md = uhd.types.TXMetadata()
                tx_md.has_time_spec = True
                tx_md.time_spec = t3
                tx_streamer.send(ref_signal, tx_md)
                
                print(f"Poll detected! Sent response at hardware time: {t3.get_real_secs():.6f}")

# Main execution for Pi 2
# ref_signal = generate_zc_sequence(127, 29)
# run_responder(setup_responder(), ref_signal)

if __name__ == "__main__":
    ref_signal = generate_zc_sequence(127, 29)
    usrp_instance = setup_responder()
    
    time.sleep(1)
    run_responder(usrp_instance, ref_signal)