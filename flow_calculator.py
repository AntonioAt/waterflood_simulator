"""
flow_calculator.py
------------------
Fractional flow, mobility, gravity correction, and capillary flux
calculations for two-phase oil-water flow.
"""

from typing import Tuple
import numpy as np

from config import SimulationConfig
from relative_permeability import RelativePermeability
from capillary_pressure import CapillaryPressure


class FlowCalculator:
    """Central flow-property calculator used by the saturation updater."""

    def __init__(self, config: SimulationConfig,
                 relperm: RelativePermeability,
                 capillary: CapillaryPressure):
        self.cfg = config
        self.rp = relperm
        self.cp = capillary

    # -----------------------------------------------------------------
    # Mobilities
    # -----------------------------------------------------------------
    def mobilities(
        self, Sw: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (lambda_w, lambda_o, lambda_total)."""
        krw, kro = self.rp.both(Sw)
        lam_w = krw / self.cfg.fluid.mu_w
        lam_o = kro / self.cfg.fluid.mu_o
        return lam_w, lam_o, lam_w + lam_o

    # -----------------------------------------------------------------
    # Fractional flow
    # -----------------------------------------------------------------
    def fractional_flow(
        self, Sw: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Return (fw, lambda_total)."""
        lam_w, _, lam_t = self.mobilities(Sw)
        fw = np.where(lam_t > 0.0, lam_w / lam_t, 0.0)
        return fw, lam_t

    def dfw_dSw(self, Sw: np.ndarray, dS: float = 1e-6) -> np.ndarray:
        """Numerical derivative of fractional flow."""
        fw_p, _ = self.fractional_flow(Sw + dS)
        fw_m, _ = self.fractional_flow(Sw - dS)
        return (fw_p - fw_m) / (2.0 * dS)

    # -----------------------------------------------------------------
    # Gravity correction at internal faces
    # -----------------------------------------------------------------
    def gravity_correction(
        self, Sw: np.ndarray, lam_t: np.ndarray,
        K: np.ndarray, dx: float
    ) -> np.ndarray:
        """
        Gravity-driven flux correction at nx-1 internal faces.
        Positive when water flows downward (denser phase sinks).
        """
        if not self.cfg.gravity.enabled:
            return np.zeros(len(Sw) - 1)

        theta = np.radians(self.cfg.gravity.dip_angle)
        drho = self.cfg.fluid.rho_w - self.cfg.fluid.rho_o  # lb/ft^3
        drho_grad = drho / 144.0  # approximate psi/ft

        lam_w, lam_o, _ = self.mobilities(Sw)

        # Arithmetic averages at internal faces
        lam_w_f = 0.5 * (lam_w[:-1] + lam_w[1:])
        lam_o_f = 0.5 * (lam_o[:-1] + lam_o[1:])
        lam_t_f = 0.5 * (lam_t[:-1] + lam_t[1:])
        K_f = 0.5 * (K[:-1] + K[1:])

        safe_lam_t = np.where(lam_t_f > 0, lam_t_f, 1e-20)
        return K_f * lam_w_f * lam_o_f / safe_lam_t * drho_grad * np.sin(theta)

    # -----------------------------------------------------------------
    # Capillary flux at internal faces
    # -----------------------------------------------------------------
    def capillary_flux(
        self, Sw: np.ndarray, K: np.ndarray, dx: float
    ) -> np.ndarray:
        """
        Capillary-pressure-driven flux at nx-1 internal faces.
        Fc = -1.127e-3 * K_face * lam_w_face * dPc/dx
        """
        if not self.cfg.capillary.enabled:
            return np.zeros(len(Sw) - 1)

        lam_w, _, _ = self.mobilities(Sw)
        Pc_vals = self.cp.Pc(Sw)

        lam_w_f = 0.5 * (lam_w[:-1] + lam_w[1:])
        K_f = 0.5 * (K[:-1] + K[1:])
        dPc_dx = (Pc_vals[1:] - Pc_vals[:-1]) / dx

        return -1.127e-3 * K_f * lam_w_f * dPc_dx