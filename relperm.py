"""
relperm.py
==========
Corey relative permeability calculations.
Attaches to main via: from relperm import RelativePermeability
"""

import numpy as np
from typing import Dict, Tuple

from config import RelPermParams


class RelativePermeability:
    """Computes and caches Corey relative permeability."""

    def __init__(self, params: RelPermParams):
        self.p = params

    def _normalize(self, Sw: np.ndarray) -> np.ndarray:
        Sn = (Sw - self.p.Swc) / (1.0 - self.p.Swc - self.p.Sor)
        return np.clip(Sn, 0.0, 1.0)

    def krw(self, Sw: np.ndarray) -> np.ndarray:
        return self.p.krw_max * self._normalize(Sw) ** self.p.nw

    def kro(self, Sw: np.ndarray) -> np.ndarray:
        return self.p.kro_max * (1.0 - self._normalize(Sw)) ** self.p.no

    def both(self, Sw: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        Sn = self._normalize(Sw)
        return (
            self.p.krw_max * Sn ** self.p.nw,
            self.p.kro_max * (1.0 - Sn) ** self.p.no
        )

    def tabulate(self, n: int = 200) -> Dict[str, np.ndarray]:
        """Return tabulated curves for plotting / export."""
        Sw = np.linspace(self.p.Swc, 1.0 - self.p.Sor, n)
        krw, kro = self.both(Sw)
        return {"Sw": Sw, "krw": krw, "kro": kro}