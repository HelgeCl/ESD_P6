import numpy as np
from Generate_Samples import sample_gen
from DoA import esprit
import time


trials = 1000000
esprit_results = []
runtimes = []


for _ in range(trials):
    angle = np.random.uniform(-50, 50)
    rx = sample_gen(2, 120e3, 200, angle, 14, 0.5)
    t0 = time.perf_counter()
    esprit_results.append(esprit(rx, 1))
    t1 = time.perf_counter()
    runtimes.append(t1-t0)

print("Average: ", np.average(runtimes))
print("Max: ", np.max(runtimes))
print("Min: ", np.min(runtimes))
