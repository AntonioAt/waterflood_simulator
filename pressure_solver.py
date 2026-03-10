"""
pressure_solver.py
==================
Simple IMPES-style pressure equation for incompressible 2-phase flow.
Attaches to main via: from pressure_solver import PressureSolver
"""

import numpy as np
from typing import Tuple

from config import SimulationConfig
from grid import Grid


class PressureSolver:
    """
    Solves:  T_{i-1/2}(p_{i-1}-p_i) + T_{i+1/2}(p_{i+1}-p_i) + Q_i = 0
    with transmissibilities T = 1.127e-3 * K_face * A * lam_t_face / dx
    """

    def __init__(self, grid: Grid, config: SimulationConfig):
        self.grid = grid
        self.cfg = config
        self.darcy_factor = 1.127e-3

    def solve(self, Sw: np.ndarray,
              lam_t: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Solve pressure and return (pressure_array, total_injection_rate).
        """
        nx = self.grid.nx
        dx = self.grid.dx
        A = self.grid.area
        wells = self.cfg.wells

        # Face transmissibilities (internal)
        K_f = self.grid.face_perm()
        lam_t_f = 0.5 * (lam_t[:-1] + lam_t[1:])
        T_f = self.darcy_factor * K_f * A * lam_t_f / dx

        # Build tridiagonal system  Ap = b
        diag = np.zeros(nx)
        upper = np.zeros(nx - 1)
        lower = np.zeros(nx - 1)
        rhs = np.zeros(nx)

        # Internal faces
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

        # Solve tridiagonal system
        pressure = self._solve_tridiag(lower, diag, upper, rhs)

        # Compute injection rate
        q_inj = PI_inj * (wells.bhp_inj - pressure[0])
        return pressure, q_inj

    @staticmethod
    def _solve_tridiag(a, b, c, d):
        """Thomas algorithm for tridiagonal system."""
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