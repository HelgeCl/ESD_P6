import uhd
import numpy as np
from BPSK import BPSK
class SDR:
    def __init__(self, master_clock_rate=200e6, tx_gain=10, rx_gain=20):
        self.usrp = uhd.usrp.MultiUSRP("type=b210")
        self.usrp.set_master_clock_rate(master_clock_rate, 0)

        self.usrp.set_tx_gain(tx_gain, 0)
        self.usrp.set_rx_gain(rx_gain, 0)
        self.usrp.set_tx_gain(30)  # Set gain (adjust as needed)
        self.usrp.set_tx_rate(1e6)                                   # Set sample rate
        self.usrp.set_tx_freq(uhd.types.TuneRequest(5.8e9))          # Set center frequency
        self.usrp.set_rx_rate(1e6)                                   # Set sample rate
        self.usrp.set_rx_freq(uhd.types.TuneRequest(5.8e9))          # Set center frequency

        self.bpsk = BPSK(fs=1e6, fc=100e3, num_symbols=100)

    def TX(self, encoded_packet, channel):
        """Transmit the given signal"""
        # Ensure signal is in the correct format (complex64)

        encoded_packet_bits = np.unpackbits(np.frombuffer(encoded_packet, dtype=np.uint8))

        modulated_signal = self.bpsk.modulate(bits = encoded_packet_bits)
        
        if modulated_signal.dtype != np.complex64:
            modulated_signal = modulated_signal.astype(np.complex64)
        
        
        
        # Transmit the signal
        self.usrp.send(modulated_signal, channel=channel)

        return modulated_signal  # Return the transmitted signal for reference

    def RX(self, num_samples, channel):
        """Receive a signal of the given number of samples"""
        # Create a buffer to hold the received samples
        rx_buffer = np.zeros(num_samples, dtype=np.complex64)
        
        # Receive the signal
        self.usrp.recv(rx_buffer)
        
        demodulated_bits = self.bpsk.demodulate(rx_buffer)

        return demodulated_bits  # Return the received signal for reference