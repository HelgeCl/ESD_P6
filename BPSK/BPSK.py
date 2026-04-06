import numpy as np
import matplotlib.pyplot as plt
import time

class BPSK:
    def __init__(self, fs=1e6, fc=100e3, num_symbols=2):
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
        
    def modulate(self, bits):
        """Modulate bits using BPSK"""
        # Map bits to symbols: 0 -> -1, 1 -> +1
        symbols = 2 * bits - 1
        
        # Upsample
        upsampled = np.repeat(symbols, self.sps)
        
        # Modulate
        modulated = upsampled + 0j  # Convert to complex
        
        # Der skal laves noget shaping her

        return modulated
    
    def demodulate(self, signal):
        """Demodulate BPSK signal"""
        # Create carrier
        t = np.arange(len(signal)) / self.fs
        carrier = np.exp(-1j * 2 * np.pi * self.fc * t)
        
        # Downconvert
        baseband = signal * carrier
        
        # Downsample
        decimated = baseband[::self.sps]
        
        # Demodulate to bits
        bits = (np.real(decimated) > 0).astype(int)
        
        # Har lidt svært ved at se om dette funger endnu

        return bits

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