"""
capillary_pressure.py
---------------------
Brooks-Corey capillary pressure model.
"""

import numpy as np
from config import CapillaryPressureParams, RelPermParams


class CapillaryPressure:
    """Brooks-Corey capillary pressure calculator."""

    def __init__(self, params: CapillaryPressureParams, rp: RelPermParams):
        self.p = params
        self.rp = rp

    def Pc(self, Sw: np.ndarray) -> np.ndarray:
        """
        Capillary pressure: Pc(Sw) = Pc_entry * Se^(-1/lambda).
        Capped at Pc_max.
        """
        if not self.p.enabled:
            return np.zeros_like(Sw)

        Se = (Sw - self.rp.Swc) / (1.0 - self.rp.Swc - self.rp.Sor)
        Se = np.clip(Se, 1e-8, 1.0)
        Pc_val = self.p.Pc_entry * Se ** (-1.0 / self.p.lam)
        return np.clip(Pc_val, 0.0, self.p.Pc_max)

    def dPc_dSw(self, Sw: np.ndarray, dS: float = 1e-6) -> np.ndarray:
        """Numerical derivative dPc/dSw (central difference)."""
        if not self.p.enabled:
            return np.zeros_like(Sw)
        return (self.Pc(Sw + dS) - self.Pc(Sw - dS)) / (2.0 * dS)

    def tabulate(self, n: int = 200):
        """Tabulated Pc curve for plotting."""
        Sw = np.linspace(self.rp.Swc + 0.01, 1.0 - self.rp.Sor, n)
        return {"Sw": Sw, "Pc": self.Pc(Sw)}