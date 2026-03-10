"""
reporting.py
============
Print comprehensive simulation report to console.
Attaches to main via: from reporting import print_report
"""

import numpy as np

from results import SimulationResults


def print_report(res: SimulationResults):
    """Print comprehensive simulation report."""
    cfg = res.config
    pv_bbl = (
        cfg.rock.porosity * cfg.rock.area
        * cfg.rock.length * 0.178107
    )
    ooip = pv_bbl * (1 - cfg.Sw_init) / cfg.fluid.Bo

    print("\n" + "=" * 70)
    print("  WATERFLOOD SIMULATION REPORT")
    print("=" * 70)

    print("\n  --- Reservoir Parameters ---")
    print(f"  Grid blocks              : {cfg.rock.nx}")
    print(f"  Length                   : {cfg.rock.length:.0f} ft")
    print(f"  Cross-sectional area     : {cfg.rock.area:.0f} ft²")
    print(f"  Porosity                 : {cfg.rock.porosity:.3f}")
    print(f"  Perm (min/mean/max)      : {res.perm_field.min():.1f} / "
          f"{res.perm_field.mean():.1f} / {res.perm_field.max():.1f} mD")
    print(f"  Pore volume              : {pv_bbl:,.0f} bbl")
    print(f"  OOIP                     : {ooip:,.0f} STB")

    print("\n  --- Fluid Properties ---")
    print(f"  μ_water / μ_oil          : {cfg.fluid.mu_w:.2f} / "
          f"{cfg.fluid.mu_o:.2f} cp")
    print(f"  Mobility ratio           : "
          f"{(cfg.relperm.krw_max / cfg.fluid.mu_w) / (cfg.relperm.kro_max / cfg.fluid.mu_o):.2f}")
    print(f"  Bo / Bw                  : {cfg.fluid.Bo:.3f} / "
          f"{cfg.fluid.Bw:.3f}")

    print("\n  --- Rel-Perm ---")
    print(f"  Swc / Sor                : {cfg.relperm.Swc:.2f} / "
          f"{cfg.relperm.Sor:.2f}")
    print(f"  krw_max / kro_max        : {cfg.relperm.krw_max:.2f} / "
          f"{cfg.relperm.kro_max:.2f}")
    print(f"  nw / no                  : {cfg.relperm.nw:.1f} / "
          f"{cfg.relperm.no:.1f}")

    print("\n  --- Physics Enabled ---")
    print(f"  Capillary pressure       : {cfg.capillary.enabled}")
    print(f"  Gravity segregation      : {cfg.gravity.enabled}")
    print(f"  Flux scheme              : {cfg.numerical.scheme}")

    print("\n  --- Performance ---")
    print(f"  Simulation time          : {res.times[-1]:.1f} days")
    print(f"  Time steps               : {res.n_steps}")
    print(f"  Wall-clock time          : {res.wall_time:.2f} s")
    print(f"  Steps / second           : {res.n_steps / res.wall_time:.0f}")

    print("\n  --- Results ---")
    print(f"  Breakthrough time        : {res.breakthrough_time:.1f} days")
    print(f"  PV injected              : {res.pore_volumes_injected:.2f}")
    print(f"  Final oil rate           : {res.oil_rate[-1]:.1f} STB/day")
    print(f"  Final water cut          : {res.water_cut[-1] * 100:.1f} %")
    print(f"  Cumulative oil           : {res.cum_oil[-1]:,.0f} STB")
    print(f"  Recovery factor          : {res.final_recovery:.2f} %")
    print("=" * 70 + "\n")