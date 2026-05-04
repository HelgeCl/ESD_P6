import uhd
import numpy as np
import time
from scipy.signal import correlate


def generate_zc_sequence(N=127, u=29):
    n = np.arange(N)
    return np.exp(-1j * np.pi * u * n * (n + 1) / N).astype(np.complex64)

def setup_initiator():
    usrp = uhd.usrp.MultiUSRP("type=b200")
    usrp.set_master_clock_rate(32e6)
    usrp.set_rx_freq(uhd.types.TuneRequest(5.8e9), 0) # 5.8 GHz, maybe set it 5.850
    usrp.set_tx_freq(uhd.types.TuneRequest(5.8e9), 0)
    usrp.set_rx_rate(10e6)
    usrp.set_tx_rate(10e6)
    usrp.set_tx_gain(0, 0)
    usrp.set_rx_gain(30, 0)
    usrp.set_time_now(uhd.types.TimeSpec(0.0))
    return usrp

def run_initiator(usrp, signal):
    st_args = uhd.usrp.StreamArgs("fc32", "sc16")
    tx_streamer = usrp.get_tx_stream(st_args)
    rx_streamer = usrp.get_rx_stream(st_args)

    # 1. Schedule TX
    tx_md = uhd.types.TXMetadata()
    tx_md.has_time_spec = True
    t1 = usrp.get_time_now() + uhd.types.TimeSpec(0.1)
    tx_md.time_spec = t1
    tx_streamer.send(signal, tx_md)
    t1_secs = t1.get_real_secs()
    print(f"Poll sent at: {t1_secs:.6f}")

    # --- START RX STREAMING HERE ---
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_continuous)
    stream_cmd.stream_now = True
    rx_streamer.issue_stream_cmd(stream_cmd)

    # 2. Listen loop
    rx_buffer = np.zeros(20000, dtype=np.complex64)
    rx_md = uhd.types.RXMetadata()
    start_wait = time.time()
    
    while (time.time() - start_wait) < 2.0: # Increased timeout to 2s
        num_rx = rx_streamer.recv(rx_buffer, rx_md)
        if num_rx > 0 and rx_md.has_time_spec:
            corr = correlate(rx_buffer[:num_rx], signal, mode='valid') # Use actual num_rx
            mag_corr = np.abs(corr)
            peak_idx = np.argmax(mag_corr)
            
            if mag_corr[peak_idx] > 10.0:
                t4_peak = rx_md.time_spec.get_real_secs() + (peak_idx / usrp.get_rx_rate())
                print(f"Response detected at: {t4_peak:.9f}")
                
                # Math
                round_trip = t4_peak - t1_secs
                print(f"Total Round Trip: {round_trip:.9f}s")
                
                # --- STOP STREAMING ---
                stop_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_continuous)
                rx_streamer.issue_stream_cmd(stop_cmd)
                return t4_peak
                
    return None

# Main execution for Pi 1
# ref_signal = generate_zc_sequence(127, 29)
# run_initiator(setup_initiator(), ref_signal)

if __name__ == "__main__":
    # 1. Generate the shared signal
    ref_signal = generate_zc_sequence(127, 29)
    
    # 2. Initialize the hardware
    usrp_instance = setup_initiator()
    
    # 3. Start the test
    # We add a small sleep to make sure the USRP is ready
    time.sleep(1)
    run_initiator(usrp_instance, ref_signal)