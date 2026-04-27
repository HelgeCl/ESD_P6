import struct

class SPPEncoder:
    def __init__(self, version=0):
        """
        Initialize Space Packet encoder.
        :param version: CCSDS version number (3 bits, default 0 for CCSDS 133.0-B)
        """
        if not (0 <= version <= 7):
            raise ValueError("Version must be a 3-bit integer (0-7)")
        self.version = version

    def encode(self, packet_type, apid, seq_flag, sequence_count, data, 
               sec_hdr_flag, sec_hdr_data=b''):
        """
        Encode a Space Packet according to CCSDS 133.0-B.
        :param packet_type: 0 = telecommand, 1 = telemetry (1 bit)
        :param apid: Application Process Identifier (11 bits, 0-2047)
        :param seq_flag: Sequence flags (2 bits: 00=continuation, 01=first, 10=last, 11=sole)
        :param sequence_count: Packet sequence count (14 bits, 0-16383)
        :param data: User data as bytes (may be empty)
        :param sec_hdr_flag: Secondary header present flag (1 bit, 0 or 1)
        :param sec_hdr_data: Secondary header bytes (required if sec_hdr_flag == 1)
        :return: Encoded packet as bytes
        """
        # Validate arguments
        if not (0 <= apid <= 2047):
            raise ValueError("APID must be 0-2047")
        if not (0 <= sequence_count <= 16383):
            raise ValueError("Sequence count must be 0-16383")
        if not (0 <= packet_type <= 1):
            raise ValueError("Packet type must be 0 or 1")
        if not (0 <= seq_flag <= 3):
            raise ValueError("Sequence flag must be 0-3")
        if sec_hdr_flag not in (0, 1):
            raise ValueError("Secondary header flag must be 0 or 1")
        if sec_hdr_flag == 1 and not isinstance(sec_hdr_data, bytes):
            raise ValueError("Secondary header data must be bytes")

        # Build the complete data field (secondary header + user data)
        data_field = (sec_hdr_data if sec_hdr_flag else b'') + data

        if len(data_field) == 0:
            raise ValueError("Packet data field cannot be empty (need at least 1 octet of user data or secondary header)")
        
        packet_data_length = len(data_field) - 1
        if packet_data_length > 65535:
            raise ValueError("Packet data field too long (max 65536 octets)")

        # Build primary header (6 bytes)
        # First 16 bits: version (3), packet_type (1), sec_hdr_flag (1), apid (11)
        word1 = (self.version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | apid
        # Next 16 bits: seq_flag (2), sequence_count (14)
        word2 = (seq_flag << 14) | sequence_count
        # Last 16 bits: packet_data_length
        word3 = packet_data_length

        prime_header = struct.pack('>HHH', word1, word2, word3)
        
        # Assemble final packet
        packet = prime_header + data_field
        return packet


# Example usage:
if __name__ == "__main__":
    encoder = SPPEncoder(version=0)  # CCSDS version 0
    
    # Example 1: No secondary header, user data "Hello World"
    packet1 = encoder.encode(
        packet_type=0,        # telecommand
        apid=123,
        seq_flag=3,           # sole packet
        sequence_count=0,
        data=b'Fat ass monkey!',
        sec_hdr_flag=0
    )
    print("Packet without secondary header (hex):", packet1.hex())
    
    # Example 2: With a simple secondary header (e.g., timestamp as 4-byte integer)
    import time
    timestamp = int(time.time())  # seconds since epoch
    sec_hdr = struct.pack('>I', timestamp)  # 4-byte unsigned int
    packet2 = encoder.encode(
        packet_type=1,        # telemetry
        apid=456,
        seq_flag=0,           # continuation (example)
        sequence_count=42,
        data=b'I\'m fast as fuck!!!',
        sec_hdr_flag=1,
        sec_hdr_data=sec_hdr
    )
    print("Packet with secondary header (hex):", packet2.hex())
    
    # Validate packet structure: first 6 bytes = primary header
    print(f"Primary header length: 6 bytes, total packet length: {len(packet2)} bytes")