import math


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
        # Validate inputs
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
        data_field = (sec_hdr_data if sec_hdr_flag else '') + \
            ''.join(format(ord(i), '08b') for i in data)

        if len(data_field) == 0:
            raise ValueError(
                "Packet data field cannot be empty (need at least 1 octet of user data or secondary header)")

        packet_data_length = math.ceil(len(data_field)/8) - 1
        if packet_data_length > 65535:
            raise ValueError("Packet data field too long (max 65536 octets)")

        # Build primary header (6 bytes)
        # First 16 bits: version (3), packet_type (1), sec_hdr_flag (1), apid (11)
        Vers_bits = format(self.version, '03b')
        type_bit = format(packet_type, '01b')
        sec_hdr_bit = format(sec_hdr_flag, '01b')
        apid_bits = format(apid, '011b')

        word1 = Vers_bits + type_bit + sec_hdr_bit + apid_bits

        # Next 16 bits: seq_flag (2), sequence_count (14)
        seq_flag_bit = format(seq_flag, '02b')
        sequence_count_bit = format(sequence_count, '014b')
        word2 = seq_flag_bit + sequence_count_bit

        # Last 16 bits: packet_data_length
        word3 = format(packet_data_length, '016b')
        prime_header = word1 + word2 + word3

        # Assemble final packet
        packet = prime_header + data_field
        return packet


# Example usage:
if __name__ == "__main__":
    encoder = SPPEncoder(version=0)  # CCSDS version 0

    packet1 = encoder.encode(
        packet_type=0,
        apid=123,
        seq_flag=3,
        sequence_count=0,
        data="Fat ass monkey!",
        sec_hdr_flag=0
    )
