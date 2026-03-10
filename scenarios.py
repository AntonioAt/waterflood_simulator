"""
scenarios.py
============
Run multiple named scenarios and produce overlay comparison plots.
Attaches to main via: from scenarios import compare_scenarios
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict

from config import SimulationConfig
from simulator import WaterfloodSimulator


def compare_scenarios(scenarios: Dict[str, SimulationConfig],
                      save: bool = True):
    """Run multiple named scenarios and produce overlay comparison plots."""
    all_results = {}
    for name, cfg in scenarios.items():
        print(f"\n=== Running scenario: {name} ===")
        sim = WaterfloodSimulator(cfg)
        res = sim.run(verbose=False)
        all_results[name] = res
        print(
            f"    RF = {res.final_recovery:.1f}%, "
            f"BT = {res.breakthrough_time:.0f} d, "
            f"Final WCut = {res.water_cut[-1] * 100:.1f}%"
        )

    # Comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "Scenario Comparison", fontsize=16, fontweight="bold"
    )
    colors = plt.cm.Set1(np.linspace(0, 0.8, len(all_results)))

    for (name, res), c in zip(all_results.items(), colors):
        axes[0, 0].plot(
            res.x,
            list(res.saturation_snapshots.values())[-1],
            color=c, lw=2, label=name
        )
        axes[0, 1].plot(
            res.times, res.oil_rate, color=c, lw=1.5, label=name
        )
        axes[1, 0].plot(
            res.times, res.water_cut * 100, color=c, lw=1.5,
            label=name
        )
        axes[1, 1].plot(
            res.times, res.recovery_factor, color=c, lw=1.5,
            label=name
        )

    axes[0, 0].set_title("Final Saturation Profile")
    axes[0, 0].set_xlabel("Distance [ft]")
    axes[0, 0].set_ylabel("Sw")
    axes[0, 1].set_title("Oil Production Rate")
    axes[0, 1].set_xlabel("Time [days]")
    axes[0, 1].set_ylabel("STB/day")
    axes[1, 0].set_title("Water Cut")
    axes[1, 0].set_xlabel("Time [days]")
    axes[1, 0].set_ylabel("%")
    axes[1, 1].set_title("Recovery Factor")
    axes[1, 1].set_xlabel("Time [days]")
    axes[1, 1].set_ylabel("%")

    for ax in axes.flat:
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    if save:
        plt.savefig("waterflood_comparison.png", dpi=150)
    plt.show()

    return all_results