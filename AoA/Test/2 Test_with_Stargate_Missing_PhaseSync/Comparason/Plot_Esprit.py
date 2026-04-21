import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

angle = 15
dbm = -9

results_data = np.load('esprit_all_results_'+str(dbm)+'dBm.npz')


# Access a specific result
results = results_data['degree_'+str(angle)]
snr = results_data['SNR_degree_0']


results = results  # + 6.09

# 3. Gaussian Fitting
mean, sd = norm.fit(results)

# 4. Plotting
plt.figure(figsize=(6, 4))

# Histogram
n, bins, patches = plt.hist(results, bins=50, density=True, alpha=0.6,
                            color='gray', label='AoA Distribution\n(60 bins)')

# Plot the PDF (Gaussian Fit)
xmin, xmax = plt.xlim()
x = np.linspace(xmin, xmax, 100)
p = norm.pdf(x, mean, sd)
plt.plot(x, p, 'k', linewidth=2, label=f'Gaussian Fit\n$\mu={mean:.2f}, \sigma={sd:.2f}$')

sd_target = 0.2884
plt.plot(x, norm.pdf(x, mean, sd_target), 'g--', lw=2,
         label=f'Target Gaussian\n($\sigma$={sd_target})')


# Rug Plot
plt.plot(results, np.full_like(results, -0.05), '|k',
         markersize=10, alpha=0.3, label='All points (Rug plot)')

plt.axhline(0, color='black', linewidth=0.8)


plt.title(rf"ESPRIT AoA Estimates for {angle}$\degree$, {dbm}dBm")
plt.xlabel("Estimated angle (degrees)")
plt.ylabel("Probability Density")
plt.legend(loc='upper right')
plt.grid(True)
plt.show()

# 5. Print Statistics
print(rf"Mean (Estimated AoA): {mean:.4f}°")
print(rf"Standard Deviation (Noise/Error): {sd:.4f}°")
