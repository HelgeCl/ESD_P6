import struct
import numpy as np
from typing import Optional, Tuple

class SPPDecoder:
    """Decoder for Space Packet Protocol (SPP) from BPSK signals"""
    
    # SPP Primary Header constants
    PRIMARY_HEADER_SIZE = 6  # bytes
    MIN_PACKET_SIZE = 7  # bytes (header + at least 1 byte data)
    
    def __init__(self, bit_rate: int = 1000):
        """
        Initialize SPP decoder
        
        Args:
            bit_rate: Bit rate in bits per second
        """
        self.bit_rate = bit_rate
        self.buffer = []
    
    def decode(self, bits: list) -> Optional[dict]:
        """
        Decode SPP packet from bit stream
        
        Args:
            bits: List of bits (0s and 1s) from BPSK demodulation
            
        Returns:
            Dictionary containing decoded packet or None if invalid
        """
        self.buffer.extend(bits)
        """""
        print(self.buffer)

        version = self.buffer[0]
        for b in range(2):
            version += self.buffer[0+b]
        pkt_type = self.buffer[3]
        sec_header = self.buffer[4]
        apid = ''
        for b in range(11):
            apid = apid + self.buffer[b+4]
        seq_flags = ''
        for b in range(2):
            seq_flags += self.buffer[15+b]
        seq_count = ''
        for b in range(14):
            seq_count += self.buffer[17+b]
        packet_data_length = ''
        for b in range(16):
            packet_data_length += self.buffer[31+b]
        packet_data = ''
        for b in range(int(packet_data_length, 2)):
            packet_data += self.buffer[47+b]

        return {
            'version': int(version, 2),
            'type': int(pkt_type,2),
            'secondary_header': bool(sec_header),
            'apid': int(apid, 2),
            'sequence_flags': int(seq_flags, 2),
            'sequence_count': int(seq_count, 2),
            'length': int(packet_data_length, 2),
            'data': packet_data.hex()
        }
        """""
        # Parse primary header
        if len(self.buffer) < (self.PRIMARY_HEADER_SIZE * 8):
            return None
        
        header_bits = self.buffer[:48]  # First 48 bits for primary header
        header_bytes = self._bits_to_bytes(header_bits)
        
        packet_length = self._get_packet_length(header_bytes)
        total_bits_needed = (packet_length * 8) + 6*8
        
        #if len(self.buffer) < total_bits_needed:
        #    return None
        
        # Extract full packet
        packet_bits = self.buffer[:total_bits_needed]
        self.buffer = self.buffer[total_bits_needed:]
        #print(packet_bits)
        packet_bytes = self._bits_to_bytes(packet_bits)
        
        return self._parse_spp_header(packet_bytes, packet_length)
    
    
    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert bit list to bytes"""
        byte_list = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) == 8:
                byte_val = int(''.join(map(str, byte_bits)), 2)
                byte_list.append(byte_val)
        return bytes(byte_list)
    
    def _get_packet_length(self, header: bytes) -> int:
        """Extract packet length from primary header"""
        if len(header) < 6:
            return 0
        length = struct.unpack('>H', header[4:6])[0]
        return length + 1  # Length field is length - 1
    
    def _parse_spp_header(self, packet: bytes, length: int) -> dict:
        """Parse SPP primary header"""
        if len(packet) < self.PRIMARY_HEADER_SIZE:
            print("Invalid header")
            return None
        
        header = packet[:self.PRIMARY_HEADER_SIZE]
        data = packet[self.PRIMARY_HEADER_SIZE:]
        
        version = (header[0] >> 5) & 0x07
        pkt_type = (header[0] >> 4) & 0x01
        sec_header = (header[0] >> 3) & 0x01
        apid = struct.unpack('>H', bytes([header[0] & 0x07, header[1]]))[0]
        seq_flags = (header[2] >> 6) & 0x03
        seq_count = struct.unpack('>H', bytes([header[2] & 0x3F, header[3]]))[0]
        # FIX: Tighten validation. The old check (apid < 2) accepted almost any header,
        # including noise-induced false positives with apid=368, length=33064, etc.
        # We know exactly what our encoder produces, so we validate all fixed fields.
        # Relax these if you introduce new APIDs or packet types.
        if version != 0:
            return None
        if apid != 102:          # only APID our encoder uses
            return None
        if pkt_type != 0:        # always telecommand
            return None
        if seq_flags != 3:       # always sole packet
            return None
        if length > 256:         # sanity check on data length
            return None
        return {
            'version': version,
            'type': pkt_type,
            'secondary_header': bool(sec_header),
            'apid': apid,
            'sequence_flags': seq_flags,
            'sequence_count': seq_count,
            'length': length,
            'data': data.hex()
        }