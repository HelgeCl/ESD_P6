import numpy as np

def esprit(r: np.ndarray, N: int, d: float = 0.5, shift: int = 1):
    """
    ESPRIT for AoA estimation.
    args:
        r (ndarray(M,L)): Input signal matrix (M antennas, with L samples)
        N (int): amount of signals to detect
        d (float): normalized distance between each of the M antennas

    retrun:
        angle (ndarray(N)): Array of estiamted AoA in degrees for N sources. 
    """
    M, L = r.shape

    # multiply and sum:
    R = (r @ r.conj().T) / L

    # Get Qs, By getting Q then sort eigenvalues in descending order and take N top:
    Lambda, Q = np.linalg.eigh(R)
    idx = np.argsort(Lambda)[::-1]
    Q_sorted = Q[:, idx[:N]]
    Q1 = Q_sorted[:M-shift, :]
    Q2 = Q_sorted[shift:, :]

    # Make V:
    combined_Q = np.vstack((Q1.conj().T, Q2.conj().T))
    V = combined_Q @ np.hstack((Q1, Q2))

    Lambda, E = np.linalg.eigh(V)

    idx = np.argsort(Lambda)[::-1]
    E_sorted = E[:, idx]

    # Partitionen E:
    E12 = E_sorted[0:N, N:2*N]  # Top-right (noise)
    E22 = E_sorted[N:2*N, N:2*N]  # Bottom-right (noise)

    # Psi:
    Psi = -E12 @ np.linalg.inv(E22)

    # Get phi's
    phi = np.linalg.eigvals(Psi)

    # Convert phi to angle, theta = sin^-1(-phase / (2 * pi * d))
    angles_rad = np.arcsin(np.angle(phi) / (2 * np.pi * d*(shift)))
    return np.degrees(angles_rad)


def delay_and_sum(X, d, point_accuracy):
    # N is number of antennas (rows), M is number of samples (columns)
    N, M = X.shape

    theta_scan = np.linspace(-1/2*np.pi, np.pi/2, point_accuracy)
    results = []

    for theta_idx in theta_scan:
        # delay-and-sum beamformer
        w = np.exp(-2j * np.pi * d * np.arange(N) * np.sin(theta_idx))
        w = w.reshape(-1, 1)
        X_weighted = w.conj().T @ X  # applying weighters
        results.append(np.var(X_weighted))  # Power in signal, in linear units

    return theta_scan[np.argmax(results)] * 180 / np.pi  # Return max value, n.b. in degrees


def music(X, d, point_accuracy, num_signals=1, sub_array_size=None):
    """
    MUSIC DoA estimator with optional Spatial Smoothing for multipath mitigation.
    
    Parameters:
    - X: Input data matrix (N antennas x M samples)
    - d: Antenna spacing normalized by wavelength (usually 0.5)
    - point_accuracy: Number of angular points to scan
    - num_signals: Expected number of sources + strong coherent reflections
    - sub_array_size: Size of sub-arrays for spatial smoothing (None to disable)
    """
    N, M = X.shape
    
    # 1. Compute the Covariance Matrix (with optional Spatial Smoothing)
    if sub_array_size and sub_array_size < N:
        L = sub_array_size
        K = N - L + 1  # Number of sub-arrays
        R = np.zeros((L, L), dtype=complex)
        for i in range(K):
            X_sub = X[i:i+L, :]
            R += (X_sub @ X_sub.conj().T) / M
        R /= K
        effective_N = L
    else:
        R = (X @ X.conj().T) / M
        effective_N = N

    # 2. Eigenvalue Decomposition
    # eigh is used because R is Hermitian (symmetric complex)
    eigenvalues, eigenvectors = np.linalg.eigh(R)
    
    # 3. Extract the Noise Subspace
    # eigh returns eigenvalues in ascending order. 
    # The smallest (effective_N - num_signals) eigenvectors belong to the noise subspace.
    idx = np.argsort(eigenvalues)
    eigenvectors_sorted = eigenvectors[:, idx]
    
    # Noise subspace matrix (G)
    G = eigenvectors_sorted[:, :effective_N - num_signals]

    # 4. Scan the angles to find the pseudo-spectrum
    theta_scan = np.linspace(-1/2*np.pi, np.pi/2, point_accuracy)
    results = []

    for theta_idx in theta_scan:
        # Construct steering vector for the current angle
        w = np.exp(-2j * np.pi * d * np.arange(effective_N) * np.sin(theta_idx))
        w = w.reshape(-1, 1)
        
        # MUSIC Pseudo-spectrum formula: P(theta) = 1 / (w^H * G * G^H * w)
        # We take the real part because the denominator mathematically resolves to a real number
        denominator = np.real(w.conj().T @ G @ G.conj().T @ w)[0, 0]
        
        # Add a tiny epsilon to prevent division by zero at perfect peaks
        results.append(1.0 / (denominator + 1e-12))

    # 5. Return the angle of the highest peak in degrees
    return theta_scan[np.argmax(results)] * 180 / np.pi

