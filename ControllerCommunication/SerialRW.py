from time import time, sleep
from serial import Serial


def __check_serial_open(serial_inst: Serial) -> None:
    """ Checks if serial instance is open, if not tries to open
            args:
                serialInst (Serial): The serial instance in question
            returns:
                None
            On error:
                throws runtime error
    """
    if not serial_inst.isOpen():
        try:
            serial_inst.open()
        except Exception as e:
            raise RuntimeError("Error cant open serialport") from e


def serial_read(serial_inst: Serial, utf: bool = True, timeout: int = 5) -> bytes | object | None:
    """Reads serial data from a serial instance. MUST BE SET UP prior to running. 
        Args:
            serialInst (Serial): a serial Instance, defined using serial.Serial()
            utf (Bool): Default True, if true, input will be decoded using UTF. NB this also splits chars at newline ('\n') 
            timeout (int): Default 5, secounds to wait for data.
        returns: 
            if uft=true: an object containing strings split at newline
            if utf=false: raw bytes
            On timeout: None
    """
    __check_serial_open(serial_inst)

    t0 = time()
    while t0+timeout > time():
        sleep(timeout/30)  # To avoid unnessesary high CPU usage
        if serial_inst.in_waiting:
            packet = serial_inst.readline()
            if utf:
                return packet.decode('utf').split('\n')[0]
            return packet
    return None


def serial_write(serial_inst: Serial, data: bytes | str) -> None:
    """
    Writes data out to an initilized serial instance. MUST BE SET UP prior to running. 
        args:
            serialInst (Serial): a serial Instance, defined using serial.Serial()
            data (Bytes|str): data to write, either as bytes or string. NB it will be encoded using utf-8
        Returns:
            None
    """
    __check_serial_open(serial_inst)

    
    if isinstance(data, str):  # If data is string, encode it propperly
        serial_inst.write(data.encode('utf-8'))
        serial_inst.flush()
        return
    serial_inst.write(data)
    serial_inst.flush()

