"""
rock_properties.py
------------------
Permeability field generators for various heterogeneity patterns.
"""

from typing import List, Tuple
import numpy as np


def uniform_perm(nx: int, k: float) -> np.ndarray:
    """Uniform permeability field."""
    return np.full(nx, k)


def random_perm(nx: int, k_mean: float, k_std: float,
                seed: int = 42) -> np.ndarray:
    """Log-normal random permeability field."""
    rng = np.random.default_rng(seed)
    log_mean = np.log(k_mean) - 0.5 * np.log(1.0 + (k_std / k_mean) ** 2)
    log_std = np.sqrt(np.log(1.0 + (k_std / k_mean) ** 2))
    return np.exp(rng.normal(log_mean, log_std, nx))


def layered_perm(nx: int, layers: List[Tuple[float, float]]) -> np.ndarray:
    """
    Layered permeability field.

    Parameters
    ----------
    nx : int
        Number of grid cells.
    layers : list of (fraction, permeability)
        Each tuple specifies the fraction of the reservoir length
        and the corresponding permeability value.

    Returns
    -------
    np.ndarray
        Permeability array of length nx.
    """
    perm = np.empty(nx)
    idx = 0
    for frac, k in layers:
        n = max(1, int(frac * nx))
        end = min(idx + n, nx)
        perm[idx:end] = k
        idx = end
    # Fill remainder with last layer value
    if idx < nx:
        perm[idx:] = layers[-1][1]
    return perm


def channel_perm(nx: int, k_background: float, k_channel: float,
                 channel_start: float = 0.3,
                 channel_end: float = 0.6) -> np.ndarray:
    """High-permeability channel embedded in background rock."""
    perm = np.full(nx, k_background)
    i_start = int(channel_start * nx)
    i_end = int(channel_end * nx)
    perm[i_start:i_end] = k_channel
    return perm


def sinusoidal_perm(nx: int, k_mean: float, k_amplitude: float,
                    n_periods: float = 3.0) -> np.ndarray:
    """Sinusoidal permeability variation."""
    x = np.linspace(0, 2.0 * np.pi * n_periods, nx)
    return k_mean + k_amplitude * np.sin(x)