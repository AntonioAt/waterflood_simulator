"""
main.py
=======
Entry point that imports and orchestrates all branch modules.
This is the trunk — all branches attach here.
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ── Branch imports (each is an independent module) ──────────────────
from config import SimulationConfig
from permeability import (
    uniform_perm, random_perm, channel_perm, layered_perm
)
from simulator import WaterfloodSimulator
from plotting import ResultsPlotter
from reporting import print_report
from sensitivity import sensitivity_analysis
from scenarios import compare_scenarios


def main():
    print("=" * 70)
    print("  EXPANDED 1-D WATERFLOOD RESERVOIR SIMULATOR")
    print("=" * 70)

    # ──────────────────────────────────────────────────────────────────
    # CASE 1: Base-Case Waterflood (rate-controlled, uniform perm)
    # ──────────────────────────────────────────────────────────────────
    print("\n\n>>> CASE 1: Base-Case Waterflood <<<\n")
    cfg_base = SimulationConfig()
    sim = WaterfloodSimulator(cfg_base)
    res_base = sim.run(verbose=True)
    print_report(res_base)

    plotter = ResultsPlotter(res_base)
    plotter.plot_main()
    plotter.plot_diagnostics()

    # ──────────────────────────────────────────────────────────────────
    # CASE 2: Heterogeneous + Capillary + Gravity
    # ──────────────────────────────────────────────────────────────────
    print("\n\n>>> CASE 2: Heterogeneous + Capillary + Gravity <<<\n")
    cfg2 = SimulationConfig()
    cfg2.rock.perm_array = random_perm(100, 100.0, 60.0, seed=7)
    cfg2.capillary.enabled = True
    cfg2.capillary.Pc_entry = 3.0
    cfg2.gravity.enabled = True
    cfg2.gravity.dip_angle = 5.0
    cfg2.numerical.scheme = "minmod"

    sim2 = WaterfloodSimulator(cfg2)
    res2 = sim2.run(verbose=True)
    print_report(res2)
    ResultsPlotter(res2).plot_main()

    # ──────────────────────────────────────────────────────────────────
    # CASE 3: Scenario Comparison
    # ──────────────────────────────────────────────────────────────────
    print("\n\n>>> CASE 3: Scenario Comparison <<<\n")
    scenarios = {}

    # Favorable mobility
    cfg_fav = SimulationConfig()
    cfg_fav.fluid.mu_o = 0.5
    cfg_fav.fluid.mu_w = 0.5
    scenarios["Favorable (M≈0.3)"] = cfg_fav

    # Unfavorable mobility
    cfg_unfav = SimulationConfig()
    cfg_unfav.fluid.mu_o = 10.0
    scenarios["Unfavorable (M≈6)"] = cfg_unfav

    # High-perm channel
    cfg_chan = SimulationConfig()
    cfg_chan.rock.perm_array = channel_perm(100, 50, 800, 0.3, 0.7)
    scenarios["Channel (50/800 mD)"] = cfg_chan

    # Base case for reference
    scenarios["Base Case"] = SimulationConfig()

    compare_scenarios(scenarios)

    # ──────────────────────────────────────────────────────────────────
    # CASE 4: Full Sensitivity Analysis
    # ──────────────────────────────────────────────────────────────────
    print("\n\n>>> CASE 4: Sensitivity Analysis <<<\n")
    sensitivity_analysis()

    print("\n\nAll simulations and plots complete.")


if __name__ == "__main__":
    main()