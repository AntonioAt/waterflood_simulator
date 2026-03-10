"""
sensitivity.py
--------------
Automated parametric sensitivity analysis.
Sweeps key parameters and generates comparison plots.
"""

from typing import Dict
import numpy as np
import matplotlib.pyplot as plt

from config import SimulationConfig
from simulator import WaterfloodSimulator
from results import SimulationResults
from rock_properties import uniform_perm, random_perm, channel_perm, layered_perm


def run_sensitivity(base_config: SimulationConfig = None,
                    verbose: bool = False) -> Dict[str, Dict[str, SimulationResults]]:
    """
    Run five parametric sweeps and return nested results dictionary.

    Returns
    -------
    studies : dict
        {study_name: {case_label: SimulationResults}}
    """
    studies = {}

    # --- 1. Viscosity ratio ---
    print("\n>>> Sweep: Viscosity Ratio <<<")
    results = {}
    for mu_o in [0.5, 1.0, 2.0, 5.0, 10.0]:
        cfg = SimulationConfig()
        cfg.fluid.mu_o = mu_o
        M = ((cfg.relperm.krw_max / cfg.fluid.mu_w)
             / (cfg.relperm.kro_max / mu_o))
        label = f"μo={mu_o} (M={M:.2f})"
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Viscosity Ratio"] = results

    # --- 2. Corey exponents ---
    print(">>> Sweep: Corey Exponents <<<")
    results = {}
    for n in [1.5, 2.0, 3.0, 4.0]:
        cfg = SimulationConfig()
        cfg.relperm.nw = n
        cfg.relperm.no = n
        label = f"nw=no={n}"
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Corey Exponents"] = results

    # --- 3. Injection rate ---
    print(">>> Sweep: Injection Rate <<<")
    results = {}
    for q in [200, 500, 1000, 2000]:
        cfg = SimulationConfig()
        cfg.wells.q_inj = q
        label = f"q={q} bbl/d"
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Injection Rate"] = results

    # --- 4. Heterogeneity ---
    print(">>> Sweep: Heterogeneity <<<")
    nx = 100
    het_perms = {
        "Uniform 100 mD": uniform_perm(nx, 100.0),
        "Random σ=30": random_perm(nx, 100.0, 30.0),
        "Random σ=80": random_perm(nx, 100.0, 80.0),
        "Channel": channel_perm(nx, 50.0, 500.0),
        "Layered": layered_perm(nx, [(0.3, 200), (0.4, 50), (0.3, 150)]),
    }
    results = {}
    for label, perm in het_perms.items():
        cfg = SimulationConfig()
        cfg.rock.perm_array = perm
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Heterogeneity"] = results

    # --- 5. Endpoint krw ---
    print(">>> Sweep: Endpoint krw <<<")
    results = {}
    for krw in [0.1, 0.2, 0.3, 0.5, 0.8]:
        cfg = SimulationConfig()
        cfg.relperm.krw_max = krw
        label = f"krw_max={krw}"
        sim = WaterfloodSimulator(cfg)
        results[label] = sim.run(verbose=False)
    studies["Endpoint krw"] = results

    return studies


def plot_sensitivity(studies: Dict[str, Dict[str, SimulationResults]],
                     save: bool = True,
                     filename: str = "waterflood_sensitivity.png"):
    """Generate a multi-row comparison figure for all sensitivity studies."""
    n_studies = len(studies)
    fig, axes = plt.subplots(n_studies, 3, figsize=(18, 5 * n_studies))
    if n_studies == 1:
        axes = axes[np.newaxis, :]

    fig.suptitle("Sensitivity Analysis", fontsize=16, fontweight="bold")

    for row, (study_name, results_dict) in enumerate(studies.items()):
        colors = plt.cm.tab10(np.linspace(0, 1, len(results_dict)))

        # Col 0: final saturation
        ax = axes[row, 0]
        for (label, res), c in zip(results_dict.items(), colors):
            final_Sw = list(res.saturation_snapshots.values())[-1]
            ax.plot(res.x, final_Sw, color=c, lw=1.5, label=label)
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Sw (final)")
        ax.set_title(f"{study_name} — Saturation")
        ax.legend(fontsize=6, loc="upper right")
        ax.grid(True, alpha=0.3)

        # Col 1: water cut
        ax = axes[row, 1]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(res.times, res.water_cut * 100, color=c, lw=1.3, label=label)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Water Cut [%]")
        ax.set_title(f"{study_name} — Water Cut")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.3)

        # Col 2: recovery factor
        ax = axes[row, 2]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(res.times, res.recovery_factor, color=c, lw=1.3, label=label)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Recovery Factor [%]")
        ax.set_title(f"{study_name} — Recovery")
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    if save:
        plt.savefig(filename, dpi=150)
    plt.show()