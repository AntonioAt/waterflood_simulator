"""
main.py
-------
Entry point for the waterflood reservoir simulator.
Acts as the central router based on user selections from the CLI menu.
"""

import sys
import warnings
import copy

warnings.filterwarnings("ignore", category=RuntimeWarning)

from cli_interface import main_menu
from simulator import WaterfloodSimulator
from plotter import ResultsPlotter
from report import print_report

from scenarios import build_default_scenarios, run_scenarios, plot_scenario_comparison
from sensitivity import run_sensitivity, plot_sensitivity


def main():
    """Main execution pipeline."""
    try:
        action, config = main_menu()

        # ---------------------------------------------------------
        # ROUTE A: Single Custom Simulation
        # ---------------------------------------------------------
        if action in ["single", "all"]:
            print("\n" + "=" * 60)
            print("  STARTING CUSTOM WATERFLOOD SIMULATION")
            print("=" * 60)
            
            # Using deepcopy to ensure the base config remains untouched for subsequent steps
            sim = WaterfloodSimulator(copy.deepcopy(config))
            res = sim.run(verbose=True)
            print_report(res)
            
            print("\n[INFO] Generating single simulation plots...")
            plotter = ResultsPlotter(res)
            plotter.plot_main(save=True, filename="results_main.png")
            plotter.plot_diagnostics(save=True, filename="results_diagnostics.png")
            print("[SUCCESS] Plots saved as 'results_main.png' and 'results_diagnostics.png'.")

        # ---------------------------------------------------------
        # ROUTE B: Scenario Comparison
        # ---------------------------------------------------------
        if action in ["scenario", "all"]:
            print("\n" + "=" * 60)
            print("  RUNNING SCENARIO COMPARISON")
            print("=" * 60)
            
            scenarios = build_default_scenarios(base_config=config)
            all_results = run_scenarios(scenarios)
            plot_scenario_comparison(all_results, save=True, filename="results_comparison.png")
            print("\n[SUCCESS] Scenario comparison complete. Plot saved as 'results_comparison.png'.")

        # ---------------------------------------------------------
        # ROUTE C: Sensitivity Analysis
        # ---------------------------------------------------------
        if action in ["sensitivity", "all"]:
            print("\n" + "=" * 60)
            print("  RUNNING PARAMETRIC SENSITIVITY ANALYSIS (MIN/BASE/MAX)")
            print("=" * 60)
            
            studies = run_sensitivity(base_config=config)
            plot_sensitivity(studies, save=True, filename="results_sensitivity.png")
            print("\n[SUCCESS] Sensitivity analysis complete. Plot saved as 'results_sensitivity.png'.")

        print("\n" + "=" * 60)
        print("  ALL REQUESTED OPERATIONS COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\n[WARN] Simulation interrupted by user. Exiting safely...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
