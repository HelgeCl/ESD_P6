import struct
import numpy as np

class SPPDecoder:
    """Decoder for Space Packet Protocol (SPP) from BPSK signals"""

    # SPP Primary Header constants
    PRIMARY_HEADER_SIZE = 6  # bytes
    MIN_PACKET_SIZE = 7  # bytes (header + at least 1 byte data)

    def __init__(self, apid):
        """
        Initialize SPP decoder

        Args:
            bit_rate: Bit rate in bits per second
        """
        self.apid = apid

    def decode(self, bits: list):
        """
        Decode SPP packet from bit stream

        Args:
            bits: List of bits (0s and 1s) from BPSK demodulation

        Returns:
            decoded package
        """

        # Check if message is long enough
        if len(bits) < (self.MIN_PACKET_SIZE * 8):
            return None

        header_bits = bits[:self.PRIMARY_HEADER_SIZE*8]  # primary header extraction
        header_bytes = self._bits_to_bytes(header_bits)  # Convert header to bytes

        packet_length = self._get_packet_length(header_bytes) #read length of packet (as specified by the packet)
        total_bits_needed = (packet_length * 8) + self.PRIMARY_HEADER_SIZE*8

        # Extract full packet
        packet_bits = bits[:total_bits_needed]

        packet_bytes = self._bits_to_bytes(packet_bits) #Convert entire package to bytes

        return self._parse_spp_header(packet_bytes, packet_length) #Convert bytes into python object

    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert bit list to bytes"""
        bits = np.array(bits)
        # Make matrix with one byte pr. row
        byte_matrix = bits.reshape(-1, 8)
        # Reshape til et 8xN matrix

        # Vector of powers 2 [128, 64... 2,1] for vector multiplication
        powers = 2 ** np.arange(7, -1, -1)  # arange start, stop (excl.), step

        # matrix (byte), vector (powers) multiplication. Sum each row
        # axis=1, to sum accros rows and not coloums
        byte_value = np.sum(byte_matrix * powers, axis=1)

        # Convert to ascii
        byte_list = bytes(byte_value.astype(np.uint8))  # Cast into bytes type
        return byte_list

    def _get_packet_length(self, header: bytes) -> int:
        """Extract packet length from primary header"""
        length = struct.unpack('>H', header[4:6])[0] #Read the two bytes containing length
        #> "big endian" i.e. MSB first, H unsigned 2 byte int
        #[0] as unpack returns tuple. We need first item
        return length + 1  # Length field is length - 1

    def _parse_spp_header(self, packet: bytes, length: int) -> dict:
        """Parse SPP primary header"""
        header = packet[:self.PRIMARY_HEADER_SIZE]
        data = packet[self.PRIMARY_HEADER_SIZE:]

        # >> bitshift, & is bitwise
        version = (header[0] >> 5) & 0x07
        #extracts the first 3 bits as this is the version
        #Done by first shifting 5 bits to the right, then saving the last 3 bits (0x07 = Binary 00000111)
        pkt_type = (header[0] >> 4) & 0x01
        sec_header = (header[0] >> 3) & 0x01
        apid = struct.unpack('>H', bytes([header[0] & 0x07, header[1]]))[0]
        seq_flags = (header[2] >> 6) & 0x03
        seq_count = struct.unpack('>H', bytes([header[2] & 0x3F, header[3]]))[0]
        # Validate input
        if version != 0:
            return None
        if apid != self.apid:          # only APID our encoder uses
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
