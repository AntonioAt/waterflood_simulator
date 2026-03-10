"""
config.py
---------
Dataclass-based configuration objects for the waterflood simulator.
All simulation parameters are organized into domain-specific groups
and aggregated into a single SimulationConfig container.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import json


@dataclass
class RockProperties:
    nx: int = 100
    length: float = 1000.0
    area: float = 5000.0
    porosity: float = 0.20
    permeability: float = 100.0
    compressibility: float = 1e-6
    perm_array: Optional[np.ndarray] = None

@dataclass
class FluidProperties:
    mu_w: float = 0.5
    mu_o: float = 2.0
    Bw: float = 1.02
    Bo: float = 1.15
    rho_w: float = 62.4
    rho_o: float = 50.0
    cw: float = 3e-6
    co: float = 10e-6

@dataclass
class RelPermParams:
    Swc: float = 0.20
    Sor: float = 0.20
    krw_max: float = 0.30
    kro_max: float = 1.00
    nw: float = 2.0
    no: float = 2.0
    csv_filepath: Optional[str] = None

@dataclass
class CapillaryPressureParams:
    enabled: bool = False
    Pc_entry: float = 5.0
    lam: float = 2.0
    Pc_max: float = 50.0

@dataclass
class GravityParams:
    enabled: bool = False
    dip_angle: float = 0.0

@dataclass
class NumericalParams:
    dt_init: float = 0.5
    dt_max: float = 5.0
    dt_min: float = 0.001
    cfl_max: float = 0.50
    max_dSw_per_step: float = 0.05
    scheme: str = "upwind"

@dataclass
class WellControls:
    mode: str = "rate"
    q_inj: float = 500.0
    q_prod: float = 500.0
    bhp_inj: float = 4000.0
    bhp_prod: float = 1000.0
    PI_inj: float = 10.0
    PI_prod: float = 10.0
    p_init: float = 3000.0

@dataclass
class SensitivityBounds:
    """Stores all user-defined boundary conditions for advanced analyses."""
    # Sensitivity Min/Max Limits
    mu_o_min_mult: float = 0.5
    mu_o_max_mult: float = 2.0
    q_inj_min_mult: float = 0.5
    q_inj_max_mult: float = 1.5
    corey_min_offset: float = -0.5
    corey_max_offset: float = 1.0
    
    # Scenario Comparison Override Values
    fav_mu_o: float = 0.5             # Oil viscosity for Favorable case
    fav_mu_w: float = 0.5             # Water viscosity for Favorable case
    unfav_mu_o: float = 10.0          # Oil viscosity for Unfavorable case
    channel_bg_mult: float = 0.5      # Background perm multiplier for Channel
    channel_high_mult: float = 8.0    # Streak perm multiplier for Channel

@dataclass
class SimulationConfig:
    rock: RockProperties = field(default_factory=RockProperties)
    fluid: FluidProperties = field(default_factory=FluidProperties)
    relperm: RelPermParams = field(default_factory=RelPermParams)
    capillary: CapillaryPressureParams = field(default_factory=CapillaryPressureParams)
    gravity: GravityParams = field(default_factory=GravityParams)
    numerical: NumericalParams = field(default_factory=NumericalParams)
    wells: WellControls = field(default_factory=WellControls)
    bounds: SensitivityBounds = field(default_factory=SensitivityBounds)
    total_time: float = 2000.0
    Sw_init: float = 0.20

    @classmethod
    def from_json(cls, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        config = cls()
        
        if "rock" in data:
            for k, v in data["rock"].items(): setattr(config.rock, k, v)
        if "fluid" in data:
            for k, v in data["fluid"].items(): setattr(config.fluid, k, v)
        if "relperm" in data:
            for k, v in data["relperm"].items(): setattr(config.relperm, k, v)
        if "wells" in data:
            for k, v in data["wells"].items(): setattr(config.wells, k, v)
        if "bounds" in data:
            for k, v in data["bounds"].items(): setattr(config.bounds, k, v)
        if "total_time" in data:
            config.total_time = data["total_time"]
            
        return config
