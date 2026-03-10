"""
main.py
-------
Entry point for the waterflood reservoir simulator.
Demonstrates all capabilities: base case, complex physics,
scenario comparison, and sensitivity analysis.
"""

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

from config import SimulationConfig
from rock_properties import random_perm
from simulator import WaterfloodSimulator
from plotter import ResultsPlotter
from report import print_report
from scenarios import (
    build_default_scenarios,
    run_scenarios,
    plot_scenario_comparison,
)
from sensitivity import run_sensitivity, plot_sensitivity


def run_base_case():
    """Case 1: Standard waterflood with uniform permeability."""
    print("\n" + "=" * 70)
    print("  CASE 1: Base-Case Waterflood")
    print("=" * 70)

    cfg = SimulationConfig()
    sim = WaterfloodSimulator(cfg)
    res = sim.run(verbose=True)

    print_report(res)
    plotter = ResultsPlotter(res)
    plotter.plot_main(filename="case1_main.png")
    plotter.plot_diagnostics(filename="case1_diagnostics.png")
    return res


def run_complex_physics():
    """Case 2: Heterogeneous reservoir with capillary pressure and gravity."""
    print("\n" + "=" * 70)
    print("  CASE 2: Heterogeneous + Capillary + Gravity")
    print("=" * 70)

    cfg = SimulationConfig()
    cfg.rock.perm_array = random_perm(100, 100.0, 60.0, seed=7)
    cfg.capillary.enabled = True
    cfg.capillary.Pc_entry = 3.0
    cfg.gravity.enabled = True
    cfg.gravity.dip_angle = 5.0
    cfg.numerical.scheme = "minmod"

    sim = WaterfloodSimulator(cfg)
    res = sim.run(verbose=True)

    print_report(res)
    plotter = ResultsPlotter(res)
    plotter.plot_main(filename="case2_main.png")
    plotter.plot_diagnostics(filename="case2_diagnostics.png")
    return res


def run_scenario_comparison():
    """Case 3: Compare multiple reservoir scenarios."""
    print("\n" + "=" * 70)
    print("  CASE 3: Scenario Comparison")
    print("=" * 70)

    scenarios = build_default_scenarios()
    all_results = run_scenarios(scenarios)
    plot_scenario_comparison(all_results, filename="case3_comparison.png")
    return all_results


def run_full_sensitivity():
    """Case 4: Parametric sensitivity analysis."""
    print("\n" + "=" * 70)
    print("  CASE 4: Sensitivity Analysis")
    print("=" * 70)

    studies = run_sensitivity()
    plot_sensitivity(studies, filename="case4_sensitivity.png")
    return studies


def main():
    """Run all demonstration cases."""
    print("=" * 70)
    print("  EXPANDED 1-D WATERFLOOD RESERVOIR SIMULATOR")
    print("  Modular Multi-Script Version")
    print("=" * 70)

    res_base = run_base_case()
    res_complex = run_complex_physics()
    scenario_results = run_scenario_comparison()
    sensitivity_studies = run_full_sensitivity()

    print("\n" + "=" * 70)
    print("  ALL CASES COMPLETE")
    print("=" * 70)
    print("\nGenerated plots:")
    print("  - case1_main.png, case1_diagnostics.png")
    print("  - case2_main.png, case2_diagnostics.png")
    print("  - case3_comparison.png")
    print("  - case4_sensitivity.png")


if __name__ == "__main__":
    main()