"""
production.py
=============
Compute surface production rates and diagnostics.
Attaches to main via: from production import ProductionCalculator
"""

import numpy as np
from typing import Dict, Optional

from config import SimulationConfig
from flow import FlowCalculator


class ProductionCalculator:
    """Compute surface production rates and diagnostics."""

    def __init__(self, config: SimulationConfig,
                 flow_calc: FlowCalculator):
        self.cfg = config
        self.fc = flow_calc

    def compute(self, Sw: np.ndarray, q_total: float,
                pressure: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Return production metrics dictionary."""
        fw_last, _ = self.fc.fractional_flow(np.array([Sw[-1]]))
        fw_val = fw_last[0]

        Bo = self.cfg.fluid.Bo
        Bw = self.cfg.fluid.Bw

        q_water_res = q_total * fw_val
        q_oil_res = q_total * (1.0 - fw_val)

        q_water_surf = q_water_res / Bw
        q_oil_surf = q_oil_res / Bo

        water_cut = q_water_surf / (q_water_surf + q_oil_surf + 1e-30)

        fw_inj, _ = self.fc.fractional_flow(np.array([Sw[0]]))

        metrics = {
            "q_oil_surf": q_oil_surf,
            "q_water_surf": q_water_surf,
            "q_oil_res": q_oil_res,
            "q_water_res": q_water_res,
            "q_total": q_total,
            "water_cut": water_cut,
            "fw_producer": fw_val,
            "fw_injector": fw_inj[0],
            "avg_Sw": np.mean(Sw),
            "avg_pressure": (np.mean(pressure)
                             if pressure is not None else 0.0),
        }
        return metrics