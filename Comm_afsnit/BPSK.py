import numpy as np
#mport matplotlib.pyplot as plt
import time
import uhd
from scipy.signal import firwin

class BPSK:
    def __init__(self, fs=100e6, fc=5.8e9, num_symbols=1000, alpha=0.5, filter_span=10, sps = 8):
        """
        BPSK modulator/demodulator
        
        Args:
            fs: Sample rate (Hz)
            fc: Carrier frequency (Hz)
            num_symbols: Number of symbols to transmit
        """
        self.fs = fs
        self.fc = fc
        self.num_symbols = num_symbols
        self.sps = int(fs / 1e4)  # Samples per symbol
        
        self.alpha=alpha
        self.filter_span=filter_span
        num_taps = sps
        if num_taps % 2 == 0:
            num_taps += 1
        
        # Design RRC filter
        self.rrc_filter = firwin(
            num_taps,
            cutoff=1.0/self.sps,  # Correct cutoff for RRC
            window=('kaiser', alpha),  # Kaiser window is better for RRC
            pass_zero=True,
            scale=True,
            fs=2.0  # Normalized frequency (Nyquist = 1)
        )
    # Convert sync word "1ACFFC1D" to BPSK symbols once
        self.sync_hex = "1ACFFC1D"
        self.sync_symbols = self.hex_to_bpsk_symbols(self.sync_hex)
    @staticmethod
    def hex_to_bpsk_symbols(hex_string):
        """Convert hex string to BPSK symbols (+1/-1)"""
        bits = []
        for c in hex_string:
            if c.isdigit():
                val = int(c)
            else:
                val = ord(c.upper()) - ord('A') + 10
            bits.extend([(val >> i) & 1 for i in range(3, -1, -1)])
        return 2 * np.array(bits) - 1

    @staticmethod
    def find_sync_and_timing(matched, sync_symbols, sps):
        """Find best timing offset and start of sync word"""
        best_offset = 0
        best_corr = 0
        # Try all possible downsampling phases
        for offset in range(sps):
            downsampled = matched[offset::sps]
            # Cross-correlate with known sync symbols
            corr = np.correlate(downsampled, sync_symbols, mode='valid')
            peak = np.max(np.abs(corr))
            if peak > best_corr:
                best_corr = peak
                best_offset = offset
        # Now get the symbol stream for that offset
        downsampled = matched[best_offset::sps]
        corr = np.correlate(downsampled, sync_symbols, mode='valid')
        sync_start_symbol = np.argmax(np.abs(corr))
        # Return sample index in original matched array and the symbol stream from sync start
        sample_start = best_offset + sync_start_symbol * sps
        return sample_start, downsampled[sync_start_symbol:]

    def modulate(self, bits):
        """Modulate bits using BPSK"""
        # Map bits to symbols: 0 -> -1, 1 -> +1
        print(f"Packet to modulate: {bits}")
        symbols = 2 * bits - 1
        # Upsample
        upsampled = np.zeros(len(symbols) * self.sps, dtype=float)
        upsampled[::self.sps] = symbols
        # Modulate
        
        np.savetxt('symbols.txt', symbols, fmt='%.6e')
        print("Full array saved to 'symbols.txt'")
        np.savetxt('upsampled.txt', upsampled, fmt='%.6e')
        print("Full array saved to 'upsampled.txt'")
        
        # Der skal laves noget shaping her
        shaped_signal = np.convolve(upsampled,self.rrc_filter,mode='full')
        np.savetxt('shaped_signal.txt', shaped_signal, fmt='%.6e')
        print("Full array saved to 'shaped_signal.txt'")

        modulated_signal = shaped_signal + 0j  # Convert to complex
        print(f"Modulated signal: {modulated_signal}")
        return modulated_signal
    
    def demodulate(self, signal):
        """Demodulate with matched filter, sync word, and carrier correction.
        Returns:
            ndarray: Demodulated bits, or empty array if no sync word found.
        """
        try:
            signal_flat = np.asarray(signal).flatten()
            matched = np.convolve(signal_flat, self.rrc_filter, mode='full')
            delay = len(self.rrc_filter) - 1
            matched = matched[delay:]

            sample_start, all_symbols = self.find_sync_and_timing(matched, self.sync_symbols, self.sps)

            tx_sync = self.sync_symbols
            rx_sync = all_symbols[:len(tx_sync)]
            payload_symbols = all_symbols[len(tx_sync):]

            phase_error_sync = np.angle(rx_sync * np.conj(tx_sync))
            t_sync = np.arange(len(phase_error_sync))
            coeffs = np.polyfit(t_sync, np.unwrap(phase_error_sync), 1)

            t_payload = np.arange(len(payload_symbols))
            correction = np.exp(-1j * (coeffs[0] * (t_payload + len(tx_sync)) + coeffs[1]))
            corrected_payload = payload_symbols * correction

            bits = (np.real(corrected_payload) > 0).astype(int)
            return bits

        except ValueError as e:
            # No sync word found – likely no signal or very weak signal
            print(f"Demodulation warning: {e}")
            return np.array([], dtype=int)   # empty array indicates no packet

# Example usage
if __name__ == "__main__":
    bpsk = BPSK(fs=1e6, fc=100e3, num_symbols=100)
    
    # Generate random bits
    bits = np.random.randint(0, 2, bpsk.num_symbols)
    
    # Modulate with timing
    start_time = time.time()
    signal = bpsk.modulate(bits)
    modulate_time = time.time() - start_time
    
    # Demodulate with timing
    start_time = time.time()
    recovered_bits = bpsk.demodulate(signal)
    demodulate_time = time.time() - start_time
    
    # Calculate BER
    ber = np.mean(bits != recovered_bits)
    
    print(f"Pre modulated signal: {bits}")
    print(f"Modulated signal: {signal}")
    print(f"Demodulated signal: {recovered_bits}")
    print(f"Bit Error Rate: {ber}")
    print(f"Modulation time: {modulate_time:.6f} seconds")
    print(f"Demodulation time: {demodulate_time:.6f} seconds")
    print(f"Total time: {modulate_time + demodulate_time:.6f} seconds")
    