"""
plotter.py
----------
Comprehensive visualisation of simulation results.
Generates main results panels and extended diagnostic plots.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from config import SimulationConfig
from results import SimulationResults
from relative_permeability import RelativePermeability
from capillary_pressure import CapillaryPressure
from flow_calculator import FlowCalculator


class ResultsPlotter:
    """Plotting engine for waterflood simulation results."""

    def __init__(self, results: SimulationResults):
        self.res = results

    # =================================================================
    # Main 4-panel plot
    # =================================================================
    def plot_main(self, save: bool = True, filename: str = "waterflood_main.png"):
        """Saturation profiles, oil rate, water cut, cumulative oil."""
        res = self.res
        fig, axes = plt.subplots(2, 2, figsize=(15, 11))
        fig.suptitle("1-D Waterflood Simulation Results",
                     fontsize=16, fontweight="bold")

        self._plot_saturation_profiles(axes[0, 0])
        self._plot_oil_rate(axes[0, 1])
        self._plot_water_cut(axes[1, 0])
        self._plot_cumulative_oil(axes[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        if save:
            plt.savefig(filename, dpi=150)
        plt.show()

    # =================================================================
    # 9-panel diagnostic plot
    # =================================================================
    def plot_diagnostics(self, save: bool = True,
                         filename: str = "waterflood_diagnostics.png"):
        """Extended diagnostics: perm field, relperm, fw, rates, etc."""
        res = self.res
        fig = plt.figure(figsize=(17, 13))
        gs = GridSpec(3, 3, figure=fig, hspace=0.38, wspace=0.35)
        fig.suptitle("Waterflood Diagnostics", fontsize=15, fontweight="bold")

        # Row 0
        self._plot_perm_field(fig.add_subplot(gs[0, 0]))
        self._plot_relperm_curves(fig.add_subplot(gs[0, 1]))
        self._plot_fw_curve(fig.add_subplot(gs[0, 2]))

        # Row 1
        self._plot_all_rates(fig.add_subplot(gs[1, 0]))
        self._plot_cumulative_all(fig.add_subplot(gs[1, 1]))
        self._plot_avg_saturation(fig.add_subplot(gs[1, 2]))

        # Row 2
        self._plot_dt_history(fig.add_subplot(gs[2, 0]))
        self._plot_rf_vs_pvi(fig.add_subplot(gs[2, 1]))
        self._plot_wor(fig.add_subplot(gs[2, 2]))

        if save:
            plt.savefig(filename, dpi=150)
        plt.show()

    # =================================================================
    # Individual panel methods
    # =================================================================
    def _plot_saturation_profiles(self, ax):
        res = self.res
        cmap = plt.cm.plasma
        snaps = res.saturation_snapshots
        n = max(len(snaps) - 1, 1)
        for i, (label, Sw) in enumerate(snaps.items()):
            ax.plot(res.x, Sw, label=label, color=cmap(i / n), lw=1.8)
        rp = res.config.relperm
        ax.axhline(rp.Swc, color="grey", ls="--", lw=0.7)
        ax.axhline(1 - rp.Sor, color="grey", ls=":", lw=0.7)
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Water Saturation")
        ax.set_title("Saturation Profile")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(True, alpha=0.3)

    def _plot_oil_rate(self, ax):
        res = self.res
        ax.plot(res.times, res.oil_rate, color="green", lw=1.5)
        if not np.isnan(res.breakthrough_time):
            ax.axvline(res.breakthrough_time, color="red", ls="--", lw=0.8,
                       label=f"BT = {res.breakthrough_time:.0f} d")
            ax.legend()
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Oil Rate [STB/day]")
        ax.set_title("Oil Production Rate")
        ax.grid(True, alpha=0.3)

    def _plot_water_cut(self, ax):
        res = self.res
        ax.plot(res.times, res.water_cut * 100, color="blue", lw=1.5)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Water Cut [%]")
        ax.set_title("Water Cut")
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)

    def _plot_cumulative_oil(self, ax):
        res = self.res
        ax2 = ax.twinx()
        l1, = ax.plot(res.times, res.cum_oil / 1e3, color="red", lw=1.5,
                      label="Cumulative Oil")
        l2, = ax2.plot(res.times, res.recovery_factor, color="purple",
                       lw=1.5, ls="--", label="Recovery Factor")
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Cumulative Oil [Mstb]", color="red")
        ax2.set_ylabel("Recovery Factor [%]", color="purple")
        ax.legend(handles=[l1, l2], loc="center right", fontsize=9)
        ax.grid(True, alpha=0.3)

    def _plot_perm_field(self, ax):
        res = self.res
        ax.bar(res.x, res.perm_field, width=res.x[1] - res.x[0],
               color="brown", alpha=0.7)
        ax.set_xlabel("Distance [ft]")
        ax.set_ylabel("Permeability [mD]")
        ax.set_title("Permeability Field")
        ax.grid(True, alpha=0.3)

    def _plot_relperm_curves(self, ax):
        rp = RelativePermeability(self.res.config.relperm)
        tab = rp.tabulate()
        ax.plot(tab["Sw"], tab["krw"], "b-", lw=2, label="krw")
        ax.plot(tab["Sw"], tab["kro"], "g-", lw=2, label="kro")
        ax.set_xlabel("Sw")
        ax.set_ylabel("Relative Permeability")
        ax.set_title("Corey Rel-Perm")
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_fw_curve(self, ax):
        cfg = self.res.config
        rp = RelativePermeability(cfg.relperm)
        cp = CapillaryPressure(cfg.capillary, cfg.relperm)
        fc = FlowCalculator(cfg, rp, cp)
        Sw = np.linspace(cfg.relperm.Swc, 1 - cfg.relperm.Sor, 200)
        fw, _ = fc.fractional_flow(Sw)
        ax.plot(Sw, fw, "b-", lw=2)
        ax.set_xlabel("Sw")
        ax.set_ylabel("fw")
        ax.set_title("Fractional Flow Curve")
        ax.grid(True, alpha=0.3)

    def _plot_all_rates(self, ax):
        res = self.res
        ax.plot(res.times, res.oil_rate, "g-", lw=1.5, label="Oil")
        ax.plot(res.times, res.water_rate, "b-", lw=1.5, label="Water")
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Rate [STB/day]")
        ax.set_title("Production Rates")
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_cumulative_all(self, ax):
        res = self.res
        ax.plot(res.times, res.cum_oil / 1e3, "r-", lw=1.5, label="Cum Oil")
        ax.plot(res.times, res.cum_water / 1e3, "b-", lw=1.5, label="Cum Water")
        ax.plot(res.times, res.cum_injected / 1e3, "c--", lw=1.5, label="Cum Injected")
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Volume [Mstb]")
        ax.set_title("Cumulative Production")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_avg_saturation(self, ax):
        res = self.res
        ax.plot(res.times, res.avg_Sw, "b-", lw=1.5)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("Average Sw")
        ax.set_title("Average Water Saturation")
        ax.grid(True, alpha=0.3)

    def _plot_dt_history(self, ax):
        res = self.res
        ax.plot(res.times[1:], res.dt_history[1:], "k-", lw=0.8)
        ax.set_xlabel("Time [days]")
        ax.set_ylabel("dt [days]")
        ax.set_title("Time-Step History")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)

    def _plot_rf_vs_pvi(self, ax):
        res = self.res
        pv_bbl = (res.config.rock.porosity * res.config.rock.area
                  * res.config.rock.length * 0.178107)
        pvi = res.cum_injected / pv_bbl
        ax.plot(pvi, res.recovery_factor, "r-", lw=2)
        ax.set_xlabel("Pore Volumes Injected")
        ax.set_ylabel("Recovery Factor [%]")
        ax.set_title("RF vs PVI")
        ax.grid(True, alpha=0.3)

    def _plot_wor(self, ax):
        res = self.res
        wor = np.where(res.oil_rate > 1, res.water_rate / res.oil_rate, 0)
        ax.plot(res.cum_oil / 1e3, wor, "m-", lw=1.5)
        ax.set_xlabel("Cumulative Oil [Mstb]")
        ax.set_ylabel("WOR")
        ax.set_title("Water-Oil Ratio vs Cum Oil")
        ax.set_ylim(0, min(float(np.max(wor)) * 1.1 + 0.1, 50))
        ax.grid(True, alpha=0.3)