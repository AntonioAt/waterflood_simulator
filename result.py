"""
results.py
==========
Data container for all simulation output.
Attaches to main via: from results import SimulationResults
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List

from config import SimulationConfig


@dataclass
class SimulationResults:
    """Stores all output from a simulation run."""
    x: np.ndarray = None
    times: List[float] = field(default_factory=list)
    dt_history: List[float] = field(default_factory=list)
    oil_rate: List[float] = field(default_factory=list)
    water_rate: List[float] = field(default_factory=list)
    water_cut: List[float] = field(default_factory=list)
    cum_oil: List[float] = field(default_factory=list)
    cum_water: List[float] = field(default_factory=list)
    cum_injected: List[float] = field(default_factory=list)
    avg_pressure: List[float] = field(default_factory=list)
    avg_Sw: List[float] = field(default_factory=list)
    recovery_factor: List[float] = field(default_factory=list)
    saturation_snapshots: Dict[str, np.ndarray] = field(
        default_factory=dict
    )
    pressure_snapshots: Dict[str, np.ndarray] = field(
        default_factory=dict
    )
    perm_field: np.ndarray = None
    config: SimulationConfig = None
    wall_time: float = 0.0
    n_steps: int = 0

    # Derived quantities computed after simulation
    breakthrough_time: float = np.nan
    pore_volumes_injected: float = 0.0
    final_recovery: float = 0.0