"""
pressure_solver.py
------------------
IMPES-style pressure solver for incompressible two-phase flow.
Uses a tridiagonal system (Thomas algorithm) with well source terms.
"""

from typing import Tuple
import numpy as np

from config import SimulationConfig
from grid import Grid


class PressureSolver:
    """
    Solves the pressure equation:
        T_{i-1/2}(p_{i-1} - p_i) + T_{i+1/2}(p_{i+1} - p_i) + Q_i = 0

    Transmissibility: T = 1.127e-3 * K_face * A * lam_t_face / dx
    """

    DARCY_FACTOR = 1.127e-3   # unit conversion for Darcy's law

    def __init__(self, grid: Grid, config: SimulationConfig):
        self.grid = grid
        self.cfg = config

    def solve(self, Sw: np.ndarray,
              lam_t: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Solve for pressure and injection rate.

        Returns
        -------
        pressure : np.ndarray of shape (nx,)
        q_inj : float
            Total injection rate [bbl/day].
        """
        nx = self.grid.nx
        dx = self.grid.dx
        A = self.grid.area
        K = self.grid.perm
        wells = self.cfg.wells

        # Face transmissibilities
        K_f = self.grid.face_perm()
        lam_t_f = 0.5 * (lam_t[:-1] + lam_t[1:])
        T_f = self.DARCY_FACTOR * K_f * A * lam_t_f / dx

        # Tridiagonal coefficients
        diag = np.zeros(nx)
        upper = np.zeros(nx - 1)
        lower = np.zeros(nx - 1)
        rhs = np.zeros(nx)

        for i in range(nx - 1):
            upper[i] = -T_f[i]
            lower[i] = -T_f[i]
            diag[i] += T_f[i]
            diag[i + 1] += T_f[i]

        # Well terms
        PI_inj = wells.PI_inj * lam_t[0]
        PI_prod = wells.PI_prod * lam_t[-1]

        diag[0] += PI_inj
        rhs[0] += PI_inj * wells.bhp_inj

        diag[-1] += PI_prod
        rhs[-1] += PI_prod * wells.bhp_prod

        # Solve
        pressure = self._thomas(lower, diag, upper, rhs)
        q_inj = PI_inj * (wells.bhp_inj - pressure[0])

        return pressure, max(q_inj, 0.0)

    @staticmethod
    def _thomas(a: np.ndarray, b: np.ndarray,
                c: np.ndarray, d: np.ndarray) -> np.ndarray:
        """Thomas algorithm for tridiagonal linear system."""
        n = len(d)
        c_ = np.zeros(n - 1)
        d_ = np.zeros(n)

        c_[0] = c[0] / b[0]
        d_[0] = d[0] / b[0]

        for i in range(1, n):
            if i < n - 1:
                m = b[i] - a[i - 1] * c_[i - 1]
                c_[i] = c[i] / m
            else:
                m = b[i] - a[i - 1] * c_[i - 1]
            d_[i] = (d[i] - a[i - 1] * d_[i - 1]) / m

        x = np.zeros(n)
        x[-1] = d_[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_[i] - c_[i] * x[i + 1]

        return x