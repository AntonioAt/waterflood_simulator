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


@dataclass
class RockProperties:
    """Rock and formation geometry properties."""
    nx: int = 100
    length: float = 1000.0              # ft
    area: float = 5000.0                # ft^2
    porosity: float = 0.20
    permeability: float = 100.0         # mD (uniform default)
    compressibility: float = 1e-6       # 1/psi
    perm_array: Optional[np.ndarray] = None


@dataclass
class FluidProperties:
    """Oil and water PVT properties."""
    mu_w: float = 0.5       # water viscosity [cp]
    mu_o: float = 2.0       # oil viscosity   [cp]
    Bw: float = 1.02        # water FVF [rb/stb]
    Bo: float = 1.15        # oil FVF   [rb/stb]
    rho_w: float = 62.4     # water density [lb/ft^3]
    rho_o: float = 50.0     # oil density   [lb/ft^3]
    cw: float = 3e-6        # water compressibility [1/psi]
    co: float = 10e-6       # oil compressibility   [1/psi]


@dataclass
class RelPermParams:
    """Corey relative-permeability parameters."""
    Swc: float = 0.20       # connate water saturation
    Sor: float = 0.20       # residual oil saturation
    krw_max: float = 0.30   # endpoint water rel-perm
    kro_max: float = 1.00   # endpoint oil rel-perm
    nw: float = 2.0         # Corey water exponent
    no: float = 2.0         # Corey oil exponent


@dataclass
class CapillaryPressureParams:
    """Brooks-Corey capillary pressure model parameters."""
    enabled: bool = False
    Pc_entry: float = 5.0   # entry capillary pressure [psi]
    lam: float = 2.0        # pore-size distribution index
    Pc_max: float = 50.0    # maximum Pc [psi]


@dataclass
class GravityParams:
    """Gravity segregation parameters."""
    enabled: bool = False
    dip_angle: float = 0.0  # reservoir dip angle [degrees]


@dataclass
class NumericalParams:
    """Numerical solver controls."""
    dt_init: float = 0.5        # initial time step [days]
    dt_max: float = 5.0         # maximum time step [days]
    dt_min: float = 0.001       # minimum time step [days]
    cfl_max: float = 0.50       # CFL safety factor
    max_dSw_per_step: float = 0.05   # max saturation change per step
    scheme: str = "upwind"      # "upwind" or "minmod"


@dataclass
class WellControls:
    """Injection and production well settings."""
    mode: str = "rate"              # "rate" or "pressure"
    q_inj: float = 500.0           # injection rate  [bbl/day]
    q_prod: float = 500.0          # production rate [bbl/day]
    bhp_inj: float = 4000.0        # injection BHP   [psi]
    bhp_prod: float = 1000.0       # production BHP  [psi]
    PI_inj: float = 10.0           # injectivity index [bbl/day/psi]
    PI_prod: float = 10.0          # productivity index [bbl/day/psi]
    p_init: float = 3000.0         # initial reservoir pressure [psi]


@dataclass
class SimulationConfig:
    """Top-level container aggregating all sub-configurations."""
    rock: RockProperties = field(default_factory=RockProperties)
    fluid: FluidProperties = field(default_factory=FluidProperties)
    relperm: RelPermParams = field(default_factory=RelPermParams)
    capillary: CapillaryPressureParams = field(default_factory=CapillaryPressureParams)
    gravity: GravityParams = field(default_factory=GravityParams)
    numerical: NumericalParams = field(default_factory=NumericalParams)
    wells: WellControls = field(default_factory=WellControls)
    total_time: float = 2000.0      # simulation duration [days]
    Sw_init: float = 0.20           # initial water saturation