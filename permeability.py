"""
permeability.py
===============
Functions to generate various permeability fields.
Attaches to main via: from permeability import *
"""

import numpy as np
from typing import List, Tuple


def uniform_perm(nx: int, k: float) -> np.ndarray:
    """Uniform permeability field."""
    return np.full(nx, k)


def random_perm(nx: int, k_mean: float, k_std: float,
                seed: int = 42) -> np.ndarray:
    """Log-normal random permeability field."""
    rng = np.random.default_rng(seed)
    log_mean = np.log(k_mean) - 0.5 * np.log(1 + (k_std / k_mean) ** 2)
    log_std = np.sqrt(np.log(1 + (k_std / k_mean) ** 2))
    return np.exp(rng.normal(log_mean, log_std, nx))


def layered_perm(nx: int, layers: List[Tuple[float, float]]) -> np.ndarray:
    """
    Layered permeability.
    layers = [(fraction_of_length, perm_value), ...]
    """
    perm = np.empty(nx)
    idx = 0
    for frac, k in layers:
        n = max(1, int(frac * nx))
        perm[idx:idx + n] = k
        idx += n
    perm[idx:] = layers[-1][1]
    return perm


def channel_perm(nx: int, k_background: float, k_channel: float,
                 channel_start: float = 0.3,
                 channel_end: float = 0.6) -> np.ndarray:
    """High-permeability channel embedded in background."""
    perm = np.full(nx, k_background)
    i_start = int(channel_start * nx)
    i_end = int(channel_end * nx)
    perm[i_start:i_end] = k_channel
    return perm