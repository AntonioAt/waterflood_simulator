"""
plotting.py
===========
Comprehensive plotting of simulation results.
Attaches to main via: from plotting import ResultsPlotter
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from config import SimulationConfig
from results import SimulationResults
from relperm import RelativePermeability
from capillary import CapillaryPressure
from flow import FlowCalculator


class ResultsPlotter:
    """Comprehensive plotting of simulation results."""

    def __init__(self, results: SimulationResults):
        self.res = results

    def plot_main(self, save: bool = True):
        """4-panel main results plot."""
        res = self.res
        fig, axes = plt.subplots(2, 2, figsize=(15, 11))
        fig.suptitle(
            "1-D Waterflood Simulation Results",
            fontsize=16, fontweight="bold"
        )

        # 1. Saturation profiles
        ax = axes[0, 0]
        cmap = plt.cm.plasma
        snaps = res.saturation_snapshots
        n = len(snaps)
        for i, (label, Sw) in enumerate(snaps.items()):
            ax.plot(
                res.x, Sw, label=label,
                color=cmap(i / max(n - 1, 1)), linewidth=1.8
            )
        ax.axhline(
            res.config.relperm.Swc, color="grey", ls="--", lw=0.7,
            label=f"Swc = {res.config.relperm.Swc:.2f}"
        )
        ax.axhline(
            1 - res.config.relperm.Sor, color="grey", ls=":", lw=0.7,
            label=f"1-Sor = {1 - res.config.relperm.Sor:.2f}"
        )
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Water Saturation")
        ax.set_title("Water Saturation Profile")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(True, alpha=0.3)

        # 2. Oil rate
        ax = axes[0, 1]
        ax.plot(res.times, res.oil_rate, color="green", lw=1.5)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Oil Rate [STB/day]")
        ax.set_title("Oil Production Rate")
        if not np.isnan(res.breakthrough_time):
            ax.axvline(
                res.breakthrough_time, color="red", ls="--", lw=0.8,
                label=f"BT = {res.breakthrough_time:.0f} d"
            )
            ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Water cut
        ax = axes[1, 0]
        ax.plot(res.times, res.water_cut * 100, color="blue", lw=1.5)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Water Cut [%]")
        ax.set_title("Water Cut")
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)

        # 4. Cumulative oil + recovery factor
        ax = axes[1, 1]
        ax2 = ax.twinx()
        l1, = ax.plot(
            res.times, res.cum_oil / 1e3, color="red", lw=1.5,
            label="Cumulative Oil"
        )
        l2, = ax2.plot(
            res.times, res.recovery_factor, color="purple",
            lw=1.5, ls="--", label="Recovery Factor"
        )
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Cumulative Oil [Mstb]", color="red")
        ax2.set_ylabel("Recovery Factor [%]", color="purple")
        ax.legend(handles=[l1, l2], loc="center right", fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        if save:
            plt.savefig("waterflood_main.png", dpi=150)
        plt.show()

    def plot_diagnostics(self, save: bool = True):
        """Extended diagnostic plots."""
        res = self.res
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35)
        fig.suptitle(
            "Waterflood Diagnostics", fontsize=15, fontweight="bold"
        )

        # 1. Permeability field
        ax = fig.add_subplot(gs[0, 0])
        ax.bar(
            res.x, res.perm_field,
            width=res.x[1] - res.x[0], color="brown", alpha=0.7
        )
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Permeability [mD]")
        ax.set_title("Permeability Field")
        ax.grid(True, alpha=0.3)

        # 2. Relative permeability curves
        ax = fig.add_subplot(gs[0, 1])
        rp_data = res.config.relperm
        rp_obj = RelativePermeability(rp_data)
        tab = rp_obj.tabulate()
        ax.plot(tab["Sw"], tab["krw"], "b-", lw=2, label="krw")
        ax.plot(tab["Sw"], tab["kro"], "g-", lw=2, label="kro")
        ax.set_xlabel("Sw")
        ax.set_ylabel("Relative Permeability")
        ax.set_title("Corey Rel-Perm Curves")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Fractional flow curve
        ax = fig.add_subplot(gs[0, 2])
        Sw_range = np.linspace(rp_data.Swc, 1 - rp_data.Sor, 200)
        fc = FlowCalculator(
            res.config, rp_obj,
            CapillaryPressure(res.config.capillary, rp_data)
        )
        fw, _ = fc.fractional_flow(Sw_range)
        ax.plot(Sw_range, fw, "b-", lw=2)
        ax.set_xlabel("Sw")
        ax.set_ylabel("fw")
        ax.set_title("Fractional Flow Curve")
        ax.grid(True, alpha=0.3)

        # 4. Oil + Water rates
        ax = fig.add_subplot(gs[1, 0])
        ax.plot(res.times, res.oil_rate, "g-", lw=1.5, label="Oil")
        ax.plot(res.times, res.water_rate, "b-", lw=1.5, label="Water")
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Rate [STB/day]")
        ax.set_title("Production Rates")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 5. Cumulative fluids
        ax = fig.add_subplot(gs[1, 1])
        ax.plot(
            res.times, res.cum_oil / 1e3, "r-", lw=1.5,
            label="Cum Oil"
        )
        ax.plot(
            res.times, res.cum_water / 1e3, "b-", lw=1.5,
            label="Cum Water"
        )
        ax.plot(
            res.times, res.cum_injected / 1e3, "c--", lw=1.5,
            label="Cum Injected"
        )
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Volume [Mstb]")
        ax.set_title("Cumulative Production")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # 6. Average saturation
        ax = fig.add_subplot(gs[1, 2])
        ax.plot(res.times, res.avg_Sw, "b-", lw=1.5)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Average Sw")
        ax.set_title("Average Water Saturation")
        ax.grid(True, alpha=0.3)

        # 7. Time-step history
        ax = fig.add_subplot(gs[2, 0])
        ax.plot(res.times[1:], res.dt_history[1:], "k-", lw=0.8)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("dt [days]")
        ax.set_title("Time-Step History")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)

        # 8. Recovery factor vs PV injected
        ax = fig.add_subplot(gs[2, 1])
        pv_total = (
            res.config.rock.porosity * res.config.rock.area
            * res.config.rock.length * 0.178107
        )
        pvi = res.cum_injected / pv_total
        ax.plot(pvi, res.recovery_factor, "r-", lw=2)
        ax.set_xlabel("Pore Volumes Injected")
        ax.set_ylabel("Recovery Factor [%]")
        ax.set_title("RF vs PVI")
        ax.grid(True, alpha=0.3)

        # 9. WOR (water-oil ratio)
        ax = fig.add_subplot(gs[2, 2])
        wor = np.where(
            res.oil_rate > 1, res.water_rate / res.oil_rate, 0
        )
        ax.plot(res.cum_oil / 1e3, wor, "m-", lw=1.5)
        ax.set_xlabel("Cumulative Oil [Mstb]")
        ax.set_ylabel("WOR")
        ax.set_title("Water-Oil Ratio vs Cum Oil")
        ax.set_ylim(0, min(np.max(wor) * 1.1, 50))
        ax.grid(True, alpha=0.3)

        if save:
            plt.savefig("waterflood_diagnostics.png", dpi=150)
        plt.show()