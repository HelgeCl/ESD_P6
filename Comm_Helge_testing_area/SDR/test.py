import numpy as np

from Git.ESD_P6.SDR_class import SDR

sdr = SDR(1e6, 5.8e9, 60, 60)

smp = np.array(sdr.receive_num(1e6))
print(smp)
print(smp.shape)