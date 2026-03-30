import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from Generate_Samples import sample_gen
from DoA import esprit
import time


trials = 100000
esprit_results = []
angle = 50
runtimes = []


for _ in range(trials):

    rx = sample_gen(2, 120e3, 200, angle, 14, 0.5)
    t0 = time.perf_counter()
    esprit_results.append(esprit(rx, 1))
    t1 = time.perf_counter()
    runtimes.append(t1-t0)

dir = esprit_results
print("Average: ", np.average(dir))
print("Max: ", np.max(dir))
print("Min: ", np.min(dir))
print("Average_runtime: ", np.average(runtimes))

dir = np.array(esprit_results).flatten()
mu_fit, std_fit = norm.fit(dir)
print("Mu_fit: ", mu_fit, " Std_fit: ", std_fit)

# target:
mu_target = angle
std_target = 0.41

# xRange:
x = np.linspace(min(dir) - 0.5, max(dir) + 0.5, 1000)

# get probablity density functions
p_target = norm.pdf(x, mu_target, std_target)
p_fit = norm.pdf(x, mu_fit, std_fit)

# :::Plotting :::
plt.figure(figsize=(10, 6))

# Histogram
plt.hist(dir, bins=60, density=True, alpha=0.3, color='gray', label='Data Histogram')

# Gaussians (rf=raw (Ignore escape characters ect.) formatted (run {} as code))
plt.plot(x, p_target, 'r-', linewidth=2,
         label=rf'Target Gaussian ($\mu={mu_target}, \sigma={std_target}$)')
plt.plot(x, p_fit, 'b--', linewidth=2,
         label=rf'Fitted Gaussian ($\mu={mu_fit:.4f}, \sigma={std_fit:.4f}$)')

# Move all points down to "rug" level
rug_y_position = -0.05
# Full_like generates a vector same size as dir, with values rug_y, to get correct positionen on y-axis
plt.plot(dir, np.full_like(dir, rug_y_position), '|k', markersize=10, label='All points (Rug plot)')

# Draw buttom line for histogram, makes it easier to distigous it from rug plot
plt.axhline(0, color='black', linewidth=0.8)

# Set y-limit to also include the rug plot
plt.ylim(rug_y_position - 0.05, None)

plt.title(f"ESPRIT precision results, with incident angle {angle}, over {trials} trials")
plt.xlabel("Values")
plt.ylabel("Probability")
plt.legend(loc='upper right')
plt.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.show()
