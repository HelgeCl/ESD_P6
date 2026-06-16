from socket import gethostname
from Git.ESD_P6.Comm.TX_RX import RXTX
from Git.ESD_P6.Comm.SPPDecoder import SPPDecoder
from serial import Serial
import numpy as np
import matplotlib.pyplot as plt


IS_PI1 = (gethostname() == "pi1")
stepper = Serial("/dev/ttyUSB0", baudrate=115200)

threshold = 5

if IS_PI1 is True:
    decoder = SPPDecoder(102)
    radio = RXTX(tx_apid=101, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)
else:
    decoder = SPPDecoder(101)
    radio = RXTX(tx_apid=102, sample_rate=500e3, samples_pr_bit=16, down_sample_factor=2)

case = None

if IS_PI1:
    sampes = radio.sample_and_rtn(1e4)
    
    # 3. Plotting
    plt.figure(figsize=(10, 6))
    
    plt.plot(np.abs(sampes[0]), label='Abs CH1', color='blue')
    # Plot Imaginary part (Q)
    plt.plot(np.abs(sampes[1]), label='Abs CH2', color='red', linestyle='--')
    
    plt.title(f"Received Signal")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    #plt.ylim([-1, 1]) # Standard USRP range is -1 to 1
    
    plt.savefig('plot.png', dpi=300, bbox_inches='tight')
    #plt.show()
else:
    while True:
        radio.transmit("Hello")

