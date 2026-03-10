"""
relative_permeability.py
------------------------
Corey relative permeability model for oil-water two-phase flow.
"""

from typing import Dict, Tuple
import numpy as np
from config import RelPermParams


class RelativePermeability:
    """Corey-type relative permeability calculator."""

    def __init__(self, params: RelPermParams):
        self.p = params

    def _normalize(self, Sw: np.ndarray) -> np.ndarray:
        """Normalised water saturation in [0, 1]."""
        Sn = (Sw - self.p.Swc) / (1.0 - self.p.Swc - self.p.Sor)
        return np.clip(Sn, 0.0, 1.0)

    def krw(self, Sw: np.ndarray) -> np.ndarray:
        """Water relative permeability."""
        return self.p.krw_max * self._normalize(Sw) ** self.p.nw

    def kro(self, Sw: np.ndarray) -> np.ndarray:
        """Oil relative permeability."""
        return self.p.kro_max * (1.0 - self._normalize(Sw)) ** self.p.no

    def both(self, Sw: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Return (krw, kro) simultaneously."""
        Sn = self._normalize(Sw)
        return (
            self.p.krw_max * Sn ** self.p.nw,
            self.p.kro_max * (1.0 - Sn) ** self.p.no,
        )

    def tabulate(self, n: int = 200) -> Dict[str, np.ndarray]:
        """Tabulated curves for plotting / export."""
        Sw = np.linspace(self.p.Swc, 1.0 - self.p.Sor, n)
        krw_vals, kro_vals = self.both(Sw)
        return {"Sw": Sw, "krw": krw_vals, "kro": kro_vals}

    def __repr__(self) -> str:
        p = self.p
        return (
            f"RelativePermeability(Swc={p.Swc}, Sor={p.Sor}, "
            f"krw_max={p.krw_max}, kro_max={p.kro_max}, "
            f"nw={p.nw}, no={p.no})"
        )