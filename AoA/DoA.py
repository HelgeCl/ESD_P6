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

    theta_scan = np.linspace(-1*np.pi, np.pi, point_accuracy)
    results = []

    for theta_idx in theta_scan:
        # delay-and-sum beamformer
        w = np.exp(2j * np.pi * d * np.arange(N) * np.sin(theta_idx))
        X_weighted = w.conj().T @ X  # applying weighters
        results.append(np.var(X_weighted))  # Power in signal, in linear units

    return theta_scan[np.argmax(results)] * 180 / np.pi  # Return max value, n.b. in degrees
