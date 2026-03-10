"""
flow.py
=======
Fractional flow, total mobility, gravity and capillary corrections.
Attaches to main via: from flow import FlowCalculator, minmod
"""

import numpy as np
from typing import Tuple

from config import SimulationConfig
from relperm import RelativePermeability
from capillary import CapillaryPressure


def minmod(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Minmod slope limiter."""
    result = np.zeros_like(a)
    mask = (a * b) > 0
    result[mask] = np.where(
        np.abs(a[mask]) < np.abs(b[mask]), a[mask], b[mask]
    )
    return result


class FlowCalculator:
    """Compute fractional flow, total mobility, and
    gravity/capillary corrections."""

    def __init__(self, config: SimulationConfig,
                 relperm: RelativePermeability,
                 capillary: CapillaryPressure):
        self.cfg = config
        self.rp = relperm
        self.cp = capillary

    def mobilities(
        self, Sw: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Water mobility, oil mobility, total mobility."""
        krw, kro = self.rp.both(Sw)
        lam_w = krw / self.cfg.fluid.mu_w
        lam_o = kro / self.cfg.fluid.mu_o
        lam_t = lam_w + lam_o
        return lam_w, lam_o, lam_t

    def fractional_flow(
        self, Sw: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """fw and total mobility."""
        lam_w, lam_o, lam_t = self.mobilities(Sw)
        fw = np.where(lam_t > 0, lam_w / lam_t, 0.0)
        return fw, lam_t

    def gravity_correction(self, Sw: np.ndarray, lam_t: np.ndarray,
                           K: np.ndarray, dx: float) -> np.ndarray:
        """
        Gravity flux correction at cell faces (nx-1 internal faces).
        G_face = K_face * lam_w_face * lam_o_face / lam_t_face
                 * drho * g * sin(theta) / dx
        """
        if not self.cfg.gravity.enabled:
            return np.zeros(len(Sw) - 1)

        theta = np.radians(self.cfg.gravity.dip_angle)
        drho = (self.cfg.fluid.rho_w - self.cfg.fluid.rho_o)
        drho_grad = drho / 144.0  # psi/ft approximate

        lam_w, lam_o, _ = self.mobilities(Sw)

        # Arithmetic average at faces
        lam_w_f = 0.5 * (lam_w[:-1] + lam_w[1:])
        lam_o_f = 0.5 * (lam_o[:-1] + lam_o[1:])
        lam_t_f = 0.5 * (lam_t[:-1] + lam_t[1:])
        K_f = 0.5 * (K[:-1] + K[1:])

        safe_lam_t = np.where(lam_t_f > 0, lam_t_f, 1e-20)
        G = (K_f * lam_w_f * lam_o_f / safe_lam_t
             * drho_grad * np.sin(theta))
        return G

    def capillary_flux(self, Sw: np.ndarray, K: np.ndarray,
                       dx: float) -> np.ndarray:
        """
        Capillary-driven flux at internal faces.
        Fc = -K_face * lam_w_face * (dPc/dx)
        """
        if not self.cfg.capillary.enabled:
            return np.zeros(len(Sw) - 1)

        lam_w, _, _ = self.mobilities(Sw)
        Pc_vals = self.cp.Pc(Sw)

        lam_w_f = 0.5 * (lam_w[:-1] + lam_w[1:])
        K_f = 0.5 * (K[:-1] + K[1:])
        dPc_dx = (Pc_vals[1:] - Pc_vals[:-1]) / dx

        Fc = -1.127e-3 * K_f * lam_w_f * dPc_dx
        return Fc

    def dfw_dSw(self, Sw: np.ndarray, dS: float = 1e-6) -> np.ndarray:
        """Numerical derivative of fractional flow."""
        fw_p, _ = self.fractional_flow(Sw + dS)
        fw_m, _ = self.fractional_flow(Sw - dS)
        return (fw_p - fw_m) / (2.0 * dS)