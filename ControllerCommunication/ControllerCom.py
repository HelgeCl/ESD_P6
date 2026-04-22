from serial import Serial
from SerialRW.SerialRW import serial_read, serial_write

class MotorCom:
    def __init__(self, serial_inst : Serial):
        self.serial_inst = serial_inst

    def makeCommandData(self, steps: int) -> bytes:
    """ Takes the wanted steps integer, and transforms into data bytes, which can be send in through serial.
    Args:
        steps: The amount of steps in integer form 
    returns:
        returns a list of bytes i.e. if called data = makeCommandData(511)
            then the data would be print(data[0]) => 00000001(MSB) and print(data[1]) => 11111111(LSB)
            it then adds the escape character = ; meaning 00111011 or 0x3B in hex
    """
        msb = (steps >> 8) & 0xFF
        lsb = steps & 0xFF
        escchr = 0x3B & 0xFF
        return bytes([msb,lsb, escchr])
    

