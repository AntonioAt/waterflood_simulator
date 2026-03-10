"""
main.py
-------
Entry point for the waterflood reservoir simulator.
Integrates the interactive CLI menu for dynamic parameter input and 
orchestrates the simulation pipeline.
"""

import sys
import warnings

# Suppress runtime warnings from division by zero in numpy arrays (handled internally)
warnings.filterwarnings("ignore", category=RuntimeWarning)

from cli_interface import main_menu
from simulator import WaterfloodSimulator
from plotter import ResultsPlotter
from report import print_report

def main():
    """Main execution pipeline."""
    try:
        # 1. Launch the interactive menu to construct the configuration
        # This will block and wait for user input (CLI, JSON, or Excel)
        config = main_menu()

        print("\n" + "=" * 60)
        print("  STARTING WATERFLOOD SIMULATION")
        print("=" * 60)

        # 2. Instantiate the simulator engine with the user's config
        sim = WaterfloodSimulator(config)
        
        # 3. Execute the time-stepping loop
        res = sim.run(verbose=True)

        # 4. Output the detailed text report
        print_report(res)

        # 5. Generate, save, and display visualizations
        print("\n[INFO] Generating plots...")
        plotter = ResultsPlotter(res)
        
        # Plot the main 4-panel figure
        plotter.plot_main(save=True, filename="results_main.png")
        
        # Plot the extended diagnostics
        plotter.plot_diagnostics(save=True, filename="results_diagnostics.png")

        print("\n[SUCCESS] Simulation complete. Plots saved locally.")

    except KeyboardInterrupt:
        # Graceful exit if the user presses Ctrl+C
        print("\n\n[WARN] Simulation interrupted by user. Exiting safely...")
        sys.exit(1)
    except Exception as e:
        # Catch-all for unexpected runtime failures to prevent messy tracebacks
        print(f"\n[FATAL ERROR] An unexpected error occurred during execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
