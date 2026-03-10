"""
report.py
---------
Formatted console report of simulation parameters and results.
"""

import numpy as np
from results import SimulationResults


def print_report(res: SimulationResults):
    """Print a comprehensive simulation summary to the console."""
    cfg = res.config
    pv_bbl = (cfg.rock.porosity * cfg.rock.area
              * cfg.rock.length * 0.178107)

    print("\n" + "=" * 70)
    print("  WATERFLOOD SIMULATION REPORT")
    print("=" * 70)

    print("\n  --- Reservoir ---")
    print(f"  Grid blocks              : {cfg.rock.nx}")
    print(f"  Length                   : {cfg.rock.length:.0f} ft")
    print(f"  Cross-sectional area     : {cfg.rock.area:.0f} ft²")
    print(f"  Porosity                 : {cfg.rock.porosity:.3f}")
    print(f"  Perm (min/mean/max)      : {res.perm_field.min():.1f} / "
          f"{res.perm_field.mean():.1f} / {res.perm_field.max():.1f} mD")
    print(f"  Pore volume              : {pv_bbl:,.0f} bbl")
    print(f"  OOIP                     : {res.ooip:,.0f} STB")

    print("\n  --- Fluids ---")
    print(f"  μ_water / μ_oil          : {cfg.fluid.mu_w:.2f} / "
          f"{cfg.fluid.mu_o:.2f} cp")
    M = ((cfg.relperm.krw_max / cfg.fluid.mu_w)
         / (cfg.relperm.kro_max / cfg.fluid.mu_o))
    print(f"  Endpoint mobility ratio  : {M:.2f}")
    print(f"  Bo / Bw                  : {cfg.fluid.Bo:.3f} / "
          f"{cfg.fluid.Bw:.3f}")

    print("\n  --- Relative Permeability ---")
    print(f"  Swc / Sor                : {cfg.relperm.Swc:.2f} / "
          f"{cfg.relperm.Sor:.2f}")
    print(f"  krw_max / kro_max        : {cfg.relperm.krw_max:.2f} / "
          f"{cfg.relperm.kro_max:.2f}")
    print(f"  nw / no                  : {cfg.relperm.nw:.1f} / "
          f"{cfg.relperm.no:.1f}")

    print("\n  --- Physics ---")
    print(f"  Capillary pressure       : {'ON' if cfg.capillary.enabled else 'OFF'}")
    print(f"  Gravity (dip={cfg.gravity.dip_angle}°) : "
          f"{'ON' if cfg.gravity.enabled else 'OFF'}")
    print(f"  Flux scheme              : {cfg.numerical.scheme}")
    print(f"  Well control mode        : {cfg.wells.mode}")

    print("\n  --- Performance ---")
    print(f"  Simulation time          : {res.times[-1]:.1f} days")
    print(f"  Time steps               : {res.n_steps}")
    print(f"  Wall-clock time          : {res.wall_time:.2f} s")
    print(f"  Steps / second           : {res.n_steps / max(res.wall_time, 1e-6):.0f}")

    print("\n  --- Key Results ---")
    print(f"  Breakthrough time        : {res.breakthrough_time:.1f} days")
    print(f"  PV injected              : {res.pore_volumes_injected:.2f}")
    print(f"  Final oil rate           : {res.oil_rate[-1]:.1f} STB/day")
    print(f"  Final water cut          : {res.water_cut[-1] * 100:.1f} %")
    print(f"  Cumulative oil           : {res.cum_oil[-1]:,.0f} STB")
    print(f"  Cumulative water         : {res.cum_water[-1]:,.0f} STB")
    print(f"  Recovery factor          : {res.final_recovery:.2f} %")
    print("=" * 70 + "\n")