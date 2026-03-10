"""
capillary.py
============
Brooks-Corey capillary pressure model.
Attaches to main via: from capillary import CapillaryPressure
"""

import numpy as np

from config import CapillaryPressureParams, RelPermParams


class CapillaryPressure:
    """Brooks-Corey capillary pressure model."""

    def __init__(self, params: CapillaryPressureParams, rp: RelPermParams):
        self.p = params
        self.rp = rp

    def Pc(self, Sw: np.ndarray) -> np.ndarray:
        """Pc(Sw) = Pc_entry * Se^(-1/lambda), capped at Pc_max."""
        if not self.p.enabled:
            return np.zeros_like(Sw)
        Se = (Sw - self.rp.Swc) / (1.0 - self.rp.Swc - self.rp.Sor)
        Se = np.clip(Se, 1e-8, 1.0)
        Pc = self.p.Pc_entry * Se ** (-1.0 / self.p.lam)
        return np.clip(Pc, 0.0, self.p.Pc_max)

    def dPc_dSw(self, Sw: np.ndarray) -> np.ndarray:
        """Derivative dPc/dSw (central difference)."""
        if not self.p.enabled:
            return np.zeros_like(Sw)
        dS = 1e-6
        return (self.Pc(Sw + dS) - self.Pc(Sw - dS)) / (2.0 * dS)