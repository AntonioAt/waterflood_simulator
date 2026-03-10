"""
scenarios.py
------------
Run and compare multiple named simulation scenarios.
Pivots on the user-defined base configuration and custom scenario bounds.
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
    """Return a dictionary of comparison scenarios using custom bounds."""
    scenarios = {}
    b = base_config.bounds

    # --- Favorable mobility ---
    cfg = copy.deepcopy(base_config)
    cfg.fluid.mu_o = b.fav_mu_o
    cfg.fluid.mu_w = b.fav_mu_w
    M_fav = ((cfg.relperm.krw_max / cfg.fluid.mu_w) / 
             (cfg.relperm.kro_max / cfg.fluid.mu_o))
    scenarios[f"Favorable (M≈{M_fav:.1f})"] = cfg

    # --- Unfavorable mobility ---
    cfg = copy.deepcopy(base_config)
    cfg.fluid.mu_o = b.unfav_mu_o
    M_unfav = ((cfg.relperm.krw_max / cfg.fluid.mu_w) / 
               (cfg.relperm.kro_max / cfg.fluid.mu_o))
    scenarios[f"Unfavorable (M≈{M_unfav:.1f})"] = cfg

    # --- Channel heterogeneity ---
    cfg = copy.deepcopy(base_config)
    base_k = cfg.rock.permeability
    k_bg = base_k * b.channel_bg_mult
    k_ch = base_k * b.channel_high_mult
    cfg.rock.perm_array = channel_perm(cfg.rock.nx, k_bg, k_ch, 0.3, 0.7)
    scenarios[f"Channel ({k_bg:.0f}/{k_ch:.0f} mD)"] = cfg

    # --- User Base case ---
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
