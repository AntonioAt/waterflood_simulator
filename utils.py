"""
utils.py
--------
Shared utility functions used across multiple modules.
"""

import numpy as np


def minmod(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Minmod slope limiter.

    Returns
    -------
    result : np.ndarray
        Element-wise minmod: sign(a)*min(|a|,|b|) where a*b > 0, else 0.
    """
    result = np.zeros_like(a)
    mask = (a * b) > 0
    result[mask] = np.where(
        np.abs(a[mask]) < np.abs(b[mask]), a[mask], b[mask]
    )
    return result


def ft3_to_bbl(volume_ft3: float) -> float:
    """Convert cubic feet to barrels."""
    return volume_ft3 * 0.178107


def bbl_to_ft3(volume_bbl: float) -> float:
    """Convert barrels to cubic feet."""
    return volume_bbl / 0.178107