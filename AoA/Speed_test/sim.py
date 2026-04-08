import numpy as np
from Generate_Samples import sample_gen
from DoA import esprit
import time


trials = 1000000
esprit_results = []
runtimes = []


for t in range(trials):
    #print("Trial number: ", t)
    angle = np.random.uniform(-50, 50)
    rx = sample_gen(64, 120e3, 200, angle, 13, 0.5)
    t0 = time.perf_counter()
    esprit_results.append(esprit(rx, 1))
    t1 = time.perf_counter()
    runtimes.append(t1-t0)

np.savez_compressed(
    'esprit_benchmark_data.npz', 
    esprit_results=np.array(esprit_results), 
    runtimes=np.array(runtimes)

)
