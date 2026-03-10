"""
production_calculator.py
------------------------
Computes surface production rates, water cut, and related diagnostics
at the production (right) boundary.
"""

from typing import Dict, Optional
import numpy as np

from config import SimulationConfig
from flow_calculator import FlowCalculator


class ProductionCalculator:
    """Production metrics at the right-hand boundary."""

    def __init__(self, config: SimulationConfig,
                 flow_calc: FlowCalculator):
        self.cfg = config
        self.fc = flow_calc

    def compute(self, Sw: np.ndarray, q_total: float,
                pressure: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Compute all production metrics for the current time step.

        Returns
        -------
        dict with keys:
            q_oil_surf, q_water_surf, q_oil_res, q_water_res,
            q_total, water_cut, fw_producer, fw_injector,
            avg_Sw, avg_pressure
        """
        fw_last, _ = self.fc.fractional_flow(np.array([Sw[-1]]))
        fw_val = fw_last[0]

        Bo = self.cfg.fluid.Bo
        Bw = self.cfg.fluid.Bw

        q_water_res = q_total * fw_val
        q_oil_res = q_total * (1.0 - fw_val)

        q_water_surf = q_water_res / Bw
        q_oil_surf = q_oil_res / Bo

        total_surf = q_water_surf + q_oil_surf + 1e-30
        water_cut = q_water_surf / total_surf

        fw_inj, _ = self.fc.fractional_flow(np.array([Sw[0]]))

        return {
            "q_oil_surf": q_oil_surf,
            "q_water_surf": q_water_surf,
            "q_oil_res": q_oil_res,
            "q_water_res": q_water_res,
            "q_total": q_total,
            "water_cut": water_cut,
            "fw_producer": fw_val,
            "fw_injector": fw_inj[0],
            "avg_Sw": float(np.mean(Sw)),
            "avg_pressure": float(np.mean(pressure)) if pressure is not None else 0.0,
        }