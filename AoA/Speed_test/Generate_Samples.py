import numpy as np


def sample_gen(channels: int, samplerate: float, samples: int, dir_deg: float, SNR_dB: float, distance: float) -> np.ndarray:
    """Function for generating samples. This does not entail a upconversion -> downconversion, as it is a waste of computational power
    insted it is expected to already be baseband. Amplitude for sinusoid tx is 1. Includes noise modelled as AWGN
    Args:
        channels (int): amount of channels that receives the signal
        samplerate (float): samplerate each channel receives at
        samples (int): Amount of samples each channel takes
        dir_deg (float): direction in degrees from which the signal arrives from
        SNR_dB (float): SNR in dB of the signal
        distance (float): The lambda normalized distance between receivers
    returns:
        received (ndarray(channels, samples)): Data each received has received
    """

    t = np.arange(samples)/samplerate

    # tx
    theta_rad = np.deg2rad(dir_deg)  # Angle of arrival
    tx = np.exp(2j * np.pi * t)
    tx = tx.reshape(1, -1)  # make tx a row vector

    # Steering vectors
    k = np.arange(channels)
    s = np.exp(2j * np.pi * distance * k * np.sin(theta_rad))
    s = s.reshape(-1, 1)  # make s a column vector

    # rx
    X = s @ tx

    # Noise
    n = np.random.randn(channels, samples) + 1j * \
        np.random.randn(channels, samples)

    # Noise magnitude:
    power_signal = np.mean(np.abs(X)**2)
    snr_lin = 10 ** (SNR_dB / 10)  # From db power to lin
    total_noise_power = power_signal / snr_lin
    # As half should contribute imaginary noise and half real
    noise_scale = np.sqrt(total_noise_power / 2)
    # sqrt as the noise should be based on ampltiude and not power

    # Add noise (possible as AWGN)
    X_n = X + noise_scale * n

    return X_n
