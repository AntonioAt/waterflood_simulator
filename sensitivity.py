"""
sensitivity.py
==============
Parametric sweeps and sensitivity studies.
Attaches to main via: from sensitivity import sensitivity_analysis
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict

from config import SimulationConfig
from simulator import WaterfloodSimulator
from permeability import (
    uniform_perm, random_perm, channel_perm, layered_perm
)


def sensitivity_analysis(base_config: SimulationConfig = None,
                         verbose: bool = False):
    """
    Run parametric sweeps and compare key outputs.
    Varies: viscosity ratio, Corey exponents, injection rate,
    permeability heterogeneity, endpoint krw.
    """
    if base_config is None:
        base_config = SimulationConfig()

    studies = {}

    # --- Study 1: Viscosity ratio ---
    print("\n>>> Sensitivity: Viscosity Ratio <<<")
    mu_o_values = [0.5, 1.0, 2.0, 5.0, 10.0]
    results_mu = {}
    for mu_o in mu_o_values:
        cfg = SimulationConfig()
        cfg.fluid.mu_o = mu_o
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        label = (
            f"μ_o = {mu_o} cp "
            f"(M={cfg.relperm.krw_max / cfg.fluid.mu_w / (cfg.relperm.kro_max / mu_o):.2f})"
        )
        results_mu[label] = res
        if verbose:
            print(
                f"  {label}: RF = {res.final_recovery:.1f}%, "
                f"BT = {res.breakthrough_time:.0f} d"
            )
    studies["Viscosity Ratio"] = results_mu

    # --- Study 2: Corey Exponents ---
    print(">>> Sensitivity: Corey Exponents <<<")
    nw_values = [1.5, 2.0, 3.0, 4.0]
    results_nw = {}
    for nw in nw_values:
        cfg = SimulationConfig()
        cfg.relperm.nw = nw
        cfg.relperm.no = nw
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        label = f"nw = no = {nw}"
        results_nw[label] = res
    studies["Corey Exponents"] = results_nw

    # --- Study 3: Injection Rate ---
    print(">>> Sensitivity: Injection Rate <<<")
    q_values = [200, 500, 1000, 2000]
    results_q = {}
    for q in q_values:
        cfg = SimulationConfig()
        cfg.wells.q_inj = q
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        label = f"q_inj = {q} bbl/d"
        results_q[label] = res
    studies["Injection Rate"] = results_q

    # --- Study 4: Heterogeneity ---
    print(">>> Sensitivity: Heterogeneity <<<")
    het_configs = {
        "Uniform 100 mD": uniform_perm(100, 100.0),
        "Random (σ=30)": random_perm(100, 100.0, 30.0),
        "Random (σ=80)": random_perm(100, 100.0, 80.0),
        "Channel": channel_perm(100, 50.0, 500.0),
        "Layered": layered_perm(
            100, [(0.3, 200), (0.4, 50), (0.3, 150)]
        ),
    }
    results_het = {}
    for label, perm in het_configs.items():
        cfg = SimulationConfig()
        cfg.rock.perm_array = perm
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        results_het[label] = res
    studies["Heterogeneity"] = results_het

    # --- Study 5: Endpoint Permeability ---
    print(">>> Sensitivity: Endpoint krw <<<")
    krw_values = [0.1, 0.2, 0.3, 0.5, 0.8]
    results_krw = {}
    for krw in krw_values:
        cfg = SimulationConfig()
        cfg.relperm.krw_max = krw
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        label = f"krw_max = {krw}"
        results_krw[label] = res
    studies["Endpoint krw"] = results_krw

    # --- Plot all studies ---
    _plot_sensitivity(studies)

    return studies


def _plot_sensitivity(studies: Dict):
    """Generate comparison plots for sensitivity studies."""
    n_studies = len(studies)
    fig, axes = plt.subplots(n_studies, 3, figsize=(18, 5 * n_studies))
    if n_studies == 1:
        axes = axes[np.newaxis, :]

    fig.suptitle(
        "Sensitivity Analysis", fontsize=16, fontweight="bold"
    )

    for row, (study_name, results_dict) in enumerate(studies.items()):
        colors = plt.cm.tab10(np.linspace(0, 1, len(results_dict)))

        # Col 0: Saturation profiles (final)
        ax = axes[row, 0]
        for (label, res), c in zip(results_dict.items(), colors):
            final_Sw = list(res.saturation_snapshots.values())[-1]
            ax.plot(res.x, final_Sw, color=c, lw=1.5, label=label)
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Sw (final)")
        ax.set_title(f"{study_name} — Final Saturation")
        ax.legend(fontsize=6, loc="upper right")
        ax.grid(True, alpha=0.3)

        # Col 1: Water cut vs time
        ax = axes[row, 1]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(
                res.times, res.water_cut * 100, color=c, lw=1.3,
                label=label
            )
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Water Cut [%]")
        ax.set_title(f"{study_name} — Water Cut")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.3)

        # Col 2: Recovery factor vs time
        ax = axes[row, 2]
        for (label, res), c in zip(results_dict.items(), colors):
            ax.plot(
                res.times, res.recovery_factor, color=c, lw=1.3,
                label=label
            )
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Recovery Factor [%]")
        ax.set_title(f"{study_name} — Recovery Factor")
        ax.legend(fontsize=6)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig("waterflood_sensitivity.png", dpi=150)
    plt.show()