"""
saturation.py
=============
Finite-volume saturation update with upwind and minmod TVD schemes.
Attaches to main via: from saturation import SaturationUpdater
"""

import numpy as np

from config import SimulationConfig
from grid import Grid
from flow import FlowCalculator, minmod


class SaturationUpdater:
    """Finite-volume saturation update with selectable flux scheme."""

    def __init__(self, grid: Grid, config: SimulationConfig,
                 flow_calc: FlowCalculator):
        self.grid = grid
        self.cfg = config
        self.fc = flow_calc

    def compute_face_fluxes(self, Sw: np.ndarray,
                            q_total: float) -> np.ndarray:
        """
        Compute water flux at all nx+1 faces.
        Returns Fw[0..nx] in bbl/day.
        """
        nx = self.grid.nx
        scheme = self.cfg.numerical.scheme

        if scheme == "minmod":
            Fw = self._minmod_fluxes(Sw, q_total)
        else:
            Fw = self._upwind_fluxes(Sw, q_total)

        # Add gravity and capillary corrections to internal faces
        _, lam_t = self.fc.fractional_flow(Sw)
        K = self.grid.perm

        G = self.fc.gravity_correction(Sw, lam_t, K, self.grid.dx)
        Fc = self.fc.capillary_flux(Sw, K, self.grid.dx)

        A = self.grid.area
        Fw[1:nx] += (G + Fc) * A

        return Fw

    def _upwind_fluxes(self, Sw: np.ndarray,
                       q_total: float) -> np.ndarray:
        """First-order upwind fluxes."""
        nx = self.grid.nx
        Sw_face = np.empty(nx + 1)

        # Injection face
        Sw_face[0] = 1.0 - self.cfg.relperm.Sor

        # Internal faces (flow left -> right)
        Sw_face[1:nx] = Sw[:nx - 1]

        # Production face
        Sw_face[nx] = Sw[-1]

        fw_face, _ = self.fc.fractional_flow(Sw_face)
        return q_total * fw_face

    def _minmod_fluxes(self, Sw: np.ndarray,
                       q_total: float) -> np.ndarray:
        """Second-order TVD (minmod limiter) fluxes."""
        nx = self.grid.nx
        Fw = np.zeros(nx + 1)

        # Pad Sw with ghost cells for boundary
        Sw_ext = np.empty(nx + 2)
        Sw_ext[0] = 1.0 - self.cfg.relperm.Sor       # injection ghost
        Sw_ext[1:nx + 1] = Sw
        Sw_ext[nx + 1] = Sw[-1]                       # production ghost

        for i in range(nx + 1):
            iL = i       # left of face
            iR = i + 1   # right of face

            Sw_up = Sw_ext[iL]

            if 1 <= iL <= nx:
                slope_L = Sw_ext[iL] - Sw_ext[iL - 1]
                slope_R = (Sw_ext[iR] - Sw_ext[iL]
                           if iR <= nx + 1 else 0.0)
                phi_lim = minmod(
                    np.array([slope_R]), np.array([slope_L])
                )[0]
                Sw_up = Sw_ext[iL] + 0.5 * phi_lim

            Sw_up = np.clip(
                Sw_up, self.cfg.relperm.Swc,
                1.0 - self.cfg.relperm.Sor
            )
            fw_val, _ = self.fc.fractional_flow(np.array([Sw_up]))
            Fw[i] = q_total * fw_val[0]

        return Fw

    def update(self, Sw: np.ndarray, q_total: float,
               dt: float) -> np.ndarray:
        """Advance Sw by one explicit step."""
        nx = self.grid.nx
        phi = self.grid.porosity
        A = self.grid.area
        dx = self.grid.dx

        Fw = self.compute_face_fluxes(Sw, q_total)

        dSw = dt / (phi * A * dx) * (Fw[:nx] - Fw[1:nx + 1])
        Sw_new = Sw + dSw
        return np.clip(
            Sw_new, self.cfg.relperm.Swc, 1.0 - self.cfg.relperm.Sor
        )

    def adaptive_dt(self, Sw: np.ndarray, q_total: float,
                    dt_target: float) -> float:
        """CFL + max-dSw limited time step."""
        phi = self.grid.porosity
        A = self.grid.area
        dx = self.grid.dx
        num = self.cfg.numerical

        dfds = np.abs(self.fc.dfw_dSw(Sw))
        max_dfds = np.max(dfds) if np.max(dfds) > 0 else 1e-12
        dt_cfl = (num.cfl_max * phi * A * dx
                  / (abs(q_total) * max_dfds + 1e-30))

        dt = min(dt_target, dt_cfl, num.dt_max)
        dt = max(dt, num.dt_min)
        return dt