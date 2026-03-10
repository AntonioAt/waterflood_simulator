"""
sensitivity.py
--------------
Automated parametric sensitivity analysis.
Evaluates Min, Base, and Max scenarios pivoted on the user-defined base configuration.
"""

from typing import Dict
import copy
import numpy as np
import matplotlib.pyplot as plt

from config import SimulationConfig
from simulator import WaterfloodSimulator
from results import SimulationResults
from rock_properties import uniform_perm, random_perm, channel_perm


def run_sensitivity(base_config: SimulationConfig) -> Dict[str, Dict[str, SimulationResults]]:
    """
    Executes parametric sweeps evaluating Min, Base, and Max variations
    relative to the provided base configuration.
    """
    studies = {}

    print("\n>>> Sweep: Viscosity Ratio (Min, Base, Max) <<<")
    results = {}
    base_mu_o = base_config.fluid.mu_o
    test_values = {"Min": base_mu_o * 0.5, "Base": base_mu_o, "Max": base_mu_o * 2.0}

    for label, mu_o in test_values.items():
        cfg = copy.deepcopy(base_config)
        cfg.fluid.mu_o = mu_o
        M = ((cfg.relperm.krw_max / cfg.fluid.mu_w) / (cfg.relperm.kro_max / mu_o))
        full_label = f"{label} (M={M:.2f})"
        sim = WaterfloodSimulator(cfg)
        results[full_label] = sim.run(verbose=False)
    studies["Viscosity Ratio"] = results

    print(">>> Sweep: Injection Rate (Min, Base, Max) <<<")
    results = {}
    base_q = base_config.wells.q_inj
    test_values = {"Min": base_q * 0.5, "Base": base_q, "Max": base_q * 1.5}

    for label, q in test_values.items():
        cfg = copy.deepcopy(base_config)
        cfg.wells.q_inj = q
        full_label = f"{label} ({q:.0f} bbl/d)"
        sim = WaterfloodSimulator(cfg)
        results[full_label] = sim.run(verbose=False)
    studies["Injection Rate"] = results

    print(">>> Sweep: Corey Exponents (Min, Base, Max) <<<")
    results = {}
    base_n = base_config.relperm.nw
    test_values = {"Min": max(1.0, base_n - 0.5), "Base": base_n, "Max": base_n + 1.0}

    for label, n in test_values.items():
        cfg = copy.deepcopy(base_config)
        cfg.relperm.nw = n
        cfg.relperm.no = n
        full_label = f"{label} (n={n:.1f})"
        sim = WaterfloodSimulator(cfg)
        results[full_label] = sim.run(verbose=False)
    studies["Corey Exponents"] = results

    print(">>> Sweep: Heterogeneity (Min, Base, Max) <<<")
    nx = base_config.rock.nx
    base_perm = base_config.rock.permeability
    het_perms = {
        "Base (Uniform)": uniform_perm(nx, base_perm),
        "Min (Channel)": channel_perm(nx, base_perm * 0.5, base_perm * 5.0),
        "Max (Random Variance)": random_perm(nx, base_perm, 50.0)
    }
    results = {}
    for label, perm_array in het_perms.items():
        cfg = copy.deepcopy(base_config)
        cfg.rock.perm_array = perm_array
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Heterogeneity"] = results

    return studies


def plot_sensitivity(studies: Dict[str, Dict[str, SimulationResults]],
                     save: bool = True,
                     filename: str = "results_sensitivity.png"):
    """Generate a multi-row comparison figure for all sensitivity studies."""
    n_studies = len(studies)
    fig, axes = plt.subplots(n_studies, 3, figsize=(18, 5 * n_studies))
    if n_studies == 1:
        axes = axes[np.newaxis, :]

    fig.suptitle("Parametric Sensitivity Analysis (Min/Base/Max)", fontsize=16, fontweight="bold")

    for row, (study_name, results_dict) in enumerate(studies.items()):
        colors = plt.cm.tab10(np.linspace(0, 1, len(results_dict)))

        ax = axes[row, 0]
        for (label, res), c in zip(results_dict.items(), colors):
            final_Sw = list(res.saturation_snapshots.values())[-1]
            ax.plot(res.x, final_Sw, color=c, lw=1.5, label=label)
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Sw (final)")
        ax.set_title(f"{study_name} - Saturation")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        ax = axes[row, 1]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(res.times, res.water_cut * 100, color=c, lw=1.5, label=label)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Water Cut [%]")
        ax.set_title(f"{study_name} - Water Cut")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        ax = axes[row, 2]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(res.times, res.recovery_factor, color=c, lw=1.5, label=label)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Recovery Factor [%]")
        ax.set_title(f"{study_name} - Recovery")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    if save:
        plt.savefig(filename, dpi=150)
    plt.show()
