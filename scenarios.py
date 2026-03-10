"""
scenarios.py
------------
Run and compare multiple named simulation scenarios.
Pivots on the user-defined base configuration using deepcopy.
"""

from typing import Dict
import copy
import numpy as np
import matplotlib.pyplot as plt

from config import SimulationConfig
from simulator import WaterfloodSimulator
from results import SimulationResults
from rock_properties import channel_perm


def build_default_scenarios(base_config: SimulationConfig) -> Dict[str, SimulationConfig]:
    """Return a dictionary of comparison scenarios pivoted on the user base case."""
    scenarios = {}

    # Favorable mobility
    cfg = copy.deepcopy(base_config)
    cfg.fluid.mu_o = 0.5
    cfg.fluid.mu_w = 0.5
    scenarios["Favorable (M≈0.3)"] = cfg

    # Unfavorable mobility
    cfg = copy.deepcopy(base_config)
    cfg.fluid.mu_o = 10.0
    scenarios["Unfavorable (M≈6)"] = cfg

    # Channel heterogeneity based on user's base permeability
    cfg = copy.deepcopy(base_config)
    base_k = cfg.rock.permeability
    cfg.rock.perm_array = channel_perm(cfg.rock.nx, base_k * 0.5, base_k * 8.0, 0.3, 0.7)
    scenarios[f"Channel ({base_k * 0.5:.0f}/{base_k * 8.0:.0f} mD)"] = cfg

    # User Base case
    scenarios["User Base Case"] = copy.deepcopy(base_config)

    return scenarios


def run_scenarios(
    scenarios: Dict[str, SimulationConfig]
) -> Dict[str, SimulationResults]:
    """Run all scenarios and return results keyed by name."""
    all_results = {}
    for name, cfg in scenarios.items():
        print(f"\n=== Running: {name} ===")
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        all_results[name] = res
        print(f"    RF = {res.final_recovery:.1f}%, "
              f"BT = {res.breakthrough_time:.0f} d, "
              f"WCut = {res.water_cut[-1] * 100:.1f}%")
    return all_results


def plot_scenario_comparison(
    all_results: Dict[str, SimulationResults],
    save: bool = True,
    filename: str = "results_comparison.png",
):
    """Overlay comparison of multiple scenario results."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle("Scenario Comparison", fontsize=16, fontweight="bold")
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(all_results)))

    for (name, res), c in zip(all_results.items(), colors):
        final_Sw = list(res.saturation_snapshots.values())[-1]
        axes[0, 0].plot(res.x, final_Sw, color=c, lw=2, label=name)
        axes[0, 1].plot(res.times, res.oil_rate, color=c, lw=1.5, label=name)
        axes[1, 0].plot(res.times, res.water_cut * 100, color=c, lw=1.5, label=name)
        axes[1, 1].plot(res.times, res.recovery_factor, color=c, lw=1.5, label=name)

    titles = ["Final Saturation", "Oil Rate [STB/day]",
              "Water Cut [%]", "Recovery Factor [%]"]
    xlabels = ["Distance [ft]", "Time [days]", "Time [days]", "Time [days]"]
    ylabels = ["Sw", "STB/day", "%", "%"]

    for ax, title, xl, yl in zip(axes.flat, titles, xlabels, ylabels):
        ax.set_title(title)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if save:
        plt.savefig(filename, dpi=150)
    plt.show()
