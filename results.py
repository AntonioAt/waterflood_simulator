"""
results.py
----------
Dataclass container for all simulation outputs.
"""

from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

from config import SimulationConfig


@dataclass
class SimulationResults:
    """Stores all time-series outputs, snapshots, and KPIs."""

    # Spatial grid
    x: np.ndarray = None

    # Time-series arrays (populated after run, converted from lists)
    times: np.ndarray = None
    dt_history: np.ndarray = None
    oil_rate: np.ndarray = None
    water_rate: np.ndarray = None
    water_cut: np.ndarray = None
    cum_oil: np.ndarray = None
    cum_water: np.ndarray = None
    cum_injected: np.ndarray = None
    avg_pressure: np.ndarray = None
    avg_Sw: np.ndarray = None
    recovery_factor: np.ndarray = None

    # Snapshots
    saturation_snapshots: Dict[str, np.ndarray] = field(default_factory=dict)
    pressure_snapshots: Dict[str, np.ndarray] = field(default_factory=dict)

    # Metadata
    perm_field: np.ndarray = None
    config: SimulationConfig = None
    wall_time: float = 0.0
    n_steps: int = 0

    # KPIs (computed post-run)
    breakthrough_time: float = np.nan
    pore_volumes_injected: float = 0.0
    final_recovery: float = 0.0
    ooip: float = 0.0

    def compute_kpis(self):
        """Derive KPIs from stored time-series data."""
        # Breakthrough: first time water cut > 1 %
        bt_mask = self.water_cut > 0.01
        self.breakthrough_time = (
            float(self.times[bt_mask][0]) if np.any(bt_mask) else np.nan
        )

        self.final_recovery = float(self.recovery_factor[-1])

    def to_dict(self) -> dict:
        """Export key arrays as a plain dictionary (e.g. for CSV)."""
        return {
            "time_days": self.times,
            "oil_rate_stbd": self.oil_rate,
            "water_rate_stbd": self.water_rate,
            "water_cut_frac": self.water_cut,
            "cum_oil_stb": self.cum_oil,
            "cum_water_stb": self.cum_water,
            "recovery_factor_pct": self.recovery_factor,
        }