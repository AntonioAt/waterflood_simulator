"""
saturation_updater.py
---------------------
Finite-volume saturation update with first-order upwind
and second-order TVD (minmod) flux schemes.
Includes strict unit conversions for physical mass balance.
"""

import numpy as np

from config import SimulationConfig
from grid import Grid
from flow_calculator import FlowCalculator
from utils import minmod


class SaturationUpdater:
    """Explicit time-stepping update for water saturation."""

    def __init__(self, grid: Grid, config: SimulationConfig,
                 flow_calc: FlowCalculator):
        self.grid = grid
        self.cfg = config
        self.fc = flow_calc

    def compute_face_fluxes(self, Sw: np.ndarray,
                            q_total: float) -> np.ndarray:
        """Water volumetric flux at all nx+1 faces [bbl/day]."""
        nx = self.grid.nx
        scheme = self.cfg.numerical.scheme

        if scheme == "minmod":
            Fw = self._minmod_fluxes(Sw, q_total)
        else:
            Fw = self._upwind_fluxes(Sw, q_total)

        _, lam_t = self.fc.fractional_flow(Sw)
        K = self.grid.perm
        dx = self.grid.dx
        A = self.grid.area

        G = self.fc.gravity_correction(Sw, lam_t, K, dx)
        Fc = self.fc.capillary_flux(Sw, K, dx)
        Fw[1:nx] += (G + Fc) * A

        return Fw

    def _upwind_fluxes(self, Sw: np.ndarray,
                       q_total: float) -> np.ndarray:
        nx = self.grid.nx
        Sw_face = np.empty(nx + 1)
        Sw_face[0] = 1.0 - self.cfg.relperm.Sor
        Sw_face[1:nx] = Sw[:nx - 1]
        Sw_face[nx] = Sw[-1]
        fw_face, _ = self.fc.fractional_flow(Sw_face)
        return q_total * fw_face

    def _minmod_fluxes(self, Sw: np.ndarray,
                       q_total: float) -> np.ndarray:
        nx = self.grid.nx
        Fw = np.zeros(nx + 1)
        Sw_ext = np.empty(nx + 2)
        Sw_ext[0] = 1.0 - self.cfg.relperm.Sor
        Sw_ext[1:nx + 1] = Sw
        Sw_ext[nx + 1] = Sw[-1]

        Swc = self.cfg.relperm.Swc
        Sw_max = 1.0 - self.cfg.relperm.Sor

        for i in range(nx + 1):
            iL = i
            iR = i + 1
            Sw_up = Sw_ext[iL]

            if 1 <= iL <= nx:
                slope_L = Sw_ext[iL] - Sw_ext[iL - 1]
                slope_R = (Sw_ext[iR] - Sw_ext[iL]) if iR <= nx + 1 else 0.0
                phi_lim = minmod(np.array([slope_R]), np.array([slope_L]))[0]
                Sw_up = Sw_ext[iL] + 0.5 * phi_lim

            Sw_up = np.clip(Sw_up, Swc, Sw_max)
            fw_val, _ = self.fc.fractional_flow(np.array([Sw_up]))
            Fw[i] = q_total * fw_val[0]

        return Fw

    def update(self, Sw: np.ndarray, q_total: float,
               dt: float) -> np.ndarray:
        """Advance Sw by one explicit Euler step."""
        nx = self.grid.nx
        phi = self.grid.porosity
        A = self.grid.area
        dx = self.grid.dx

        # CRITICAL FIX: Convert cell volume from ft^3 to barrels (1 ft^3 = 0.178107 bbl)
        cell_pv_bbl = phi * A * dx * 0.178107

        Fw = self.compute_face_fluxes(Sw, q_total)
        
        # dSw = dt(days) / volume(bbl) * Flux(bbl/day) -> Units now perfectly cancel out
        dSw = (dt / cell_pv_bbl) * (Fw[:nx] - Fw[1:nx + 1])
        Sw_new = Sw + dSw

        return np.clip(Sw_new, self.cfg.relperm.Swc, 1.0 - self.cfg.relperm.Sor)

    def adaptive_dt(self, Sw: np.ndarray, q_total: float,
                    dt_target: float) -> float:
        """CFL + max-delta-Sw limited time step."""
        phi = self.grid.porosity
        A = self.grid.area
        dx = self.grid.dx
        num = self.cfg.numerical

        # CRITICAL FIX: Same volume conversion applied to the CFL stability limit
        cell_pv_bbl = phi * A * dx * 0.178107
        dfds = np.abs(self.fc.dfw_dSw(Sw))
        max_dfds = np.max(dfds) if np.max(dfds) > 0 else 1e-12
        
        dt_cfl = num.cfl_max * cell_pv_bbl / (abs(q_total) * max_dfds + 1e-30)

        dt = min(dt_target, dt_cfl, num.dt_max)
        return max(dt, num.dt_min)
