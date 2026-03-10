"""
simulator.py
------------
Main simulation engine that assembles all modules and runs the
explicit time-stepping loop.
"""

import time as timer
import numpy as np

from config import SimulationConfig
from grid import Grid
from relative_permeability import RelativePermeability
from capillary_pressure import CapillaryPressure
from flow_calculator import FlowCalculator
from saturation_updater import SaturationUpdater
from pressure_solver import PressureSolver
from production_calculator import ProductionCalculator
from results import SimulationResults


class WaterfloodSimulator:
    """1-D two-phase waterflood simulator."""

    def __init__(self, config: SimulationConfig = None):
        self.cfg = config if config is not None else SimulationConfig()
        self._build_modules()

    def _build_modules(self):
        """Instantiate all sub-modules from the configuration."""
        cfg = self.cfg
        self.grid = Grid(cfg.rock)
        self.relperm = RelativePermeability(cfg.relperm)
        self.cap_press = CapillaryPressure(cfg.capillary, cfg.relperm)
        self.flow_calc = FlowCalculator(cfg, self.relperm, self.cap_press)
        self.sat_updater = SaturationUpdater(self.grid, cfg, self.flow_calc)
        self.pressure_solver = PressureSolver(self.grid, cfg)
        self.prod_calc = ProductionCalculator(cfg, self.flow_calc)

    def run(self, verbose: bool = True) -> SimulationResults:
        """Execute the full simulation and return results."""
        t_wall_start = timer.perf_counter()

        cfg = self.cfg
        nx = self.grid.nx

        # ---- Initialise state ----
        Sw = np.full(nx, cfg.Sw_init)
        pressure = np.full(nx, cfg.wells.p_init)

        # ---- Volumetrics ----
        total_pv_bbl = self.grid.pore_volume_bbl()
        ooip = total_pv_bbl * (1.0 - cfg.Sw_init) / cfg.fluid.Bo

        # ---- History accumulators (lists for speed) ----
        hist = {
            "times": [0.0],
            "dt_history": [0.0],
            "oil_rate": [cfg.wells.q_inj / cfg.fluid.Bo],
            "water_rate": [0.0],
            "water_cut": [0.0],
            "cum_oil": [0.0],
            "cum_water": [0.0],
            "cum_injected": [0.0],
            "avg_pressure": [cfg.wells.p_init],
            "avg_Sw": [cfg.Sw_init],
            "recovery_factor": [0.0],
        }

        # ---- Snapshot schedule (Dynamic Buckley-Leverett Front Capture) ----
        time_1_pvi = total_pv_bbl / cfg.wells.q_inj
        
        early_snaps = np.linspace(0.1 * time_1_pvi, 0.5 * time_1_pvi, 4)
        late_snaps = np.linspace(time_1_pvi, cfg.total_time, 4)
        
        snap_times = np.unique(np.concatenate((early_snaps, late_snaps)))
        snap_times = snap_times[snap_times <= cfg.total_time]
        
        snap_idx = 0
        sat_snaps = {}
        pres_snaps = {}

        # ---- Time-stepping loop ----
        sim_time = 0.0
        step = 0
        dt_target = cfg.numerical.dt_init

        if verbose:
            self._print_header()

        while sim_time < cfg.total_time:
            # Injection rate
            if cfg.wells.mode == "pressure":
                _, lam_t = self.flow_calc.fractional_flow(Sw)
                pressure, q_total = self.pressure_solver.solve(Sw, lam_t)
            else:
                q_total = cfg.wells.q_inj

            # Adaptive time step
            dt = self.sat_updater.adaptive_dt(Sw, q_total, dt_target)
            if sim_time + dt > cfg.total_time:
                dt = cfg.total_time - sim_time

            # Update saturation
            Sw_new = self.sat_updater.update(Sw, q_total, dt)

            # Limit max saturation change
            max_change = np.max(np.abs(Sw_new - Sw))
            if (max_change > cfg.numerical.max_dSw_per_step
                    and dt > cfg.numerical.dt_min):
                scale = cfg.numerical.max_dSw_per_step / (max_change + 1e-30)
                dt *= scale
                if sim_time + dt > cfg.total_time:
                    dt = cfg.total_time - sim_time
                Sw_new = self.sat_updater.update(Sw, q_total, dt)

            Sw = Sw_new
            sim_time += dt
            step += 1

            # Production metrics
            metrics = self.prod_calc.compute(Sw, q_total, pressure)

            # Cumulative volumes (trapezoidal)
            cum_o = (hist["cum_oil"][-1]
                     + 0.5 * (hist["oil_rate"][-1] + metrics["q_oil_surf"]) * dt)
            cum_w = (hist["cum_water"][-1]
                     + 0.5 * (hist["water_rate"][-1] + metrics["q_water_surf"]) * dt)
            cum_inj = hist["cum_injected"][-1] + q_total * dt
            rf = cum_o / ooip * 100.0 if ooip > 0 else 0.0

            # Append to history
            hist["times"].append(sim_time)
            hist["dt_history"].append(dt)
            hist["oil_rate"].append(metrics["q_oil_surf"])
            hist["water_rate"].append(metrics["q_water_surf"])
            hist["water_cut"].append(metrics["water_cut"])
            hist["cum_oil"].append(cum_o)
            hist["cum_water"].append(cum_w)
            hist["cum_injected"].append(cum_inj)
            hist["avg_pressure"].append(metrics["avg_pressure"])
            hist["avg_Sw"].append(metrics["avg_Sw"])
            hist["recovery_factor"].append(rf)

            # Snapshots
            if snap_idx < len(snap_times) and sim_time >= snap_times[snap_idx]:
                label = f"t = {snap_times[snap_idx]:.0f} d"
                sat_snaps[label] = Sw.copy()
                pres_snaps[label] = pressure.copy()
                snap_idx += 1

            # Verbose progress
            if verbose:
                print_interval = max(1, int(cfg.total_time / dt / 20))
                if step % print_interval == 0 or sim_time >= cfg.total_time:
                    self._print_row(step, sim_time, dt, metrics, cum_o, rf)

            # Gradual dt growth
            dt_target = min(dt * 1.1, cfg.numerical.dt_max)

        # Final snapshot
        sat_snaps["Final"] = Sw.copy()
        pres_snaps["Final"] = pressure.copy()

        # ---- Build results object ----
        res = SimulationResults()
        res.x = self.grid.x.copy()
        res.perm_field = self.grid.perm.copy()
        res.config = cfg
        res.ooip = ooip

        for key in hist:
            setattr(res, key, np.array(hist[key]))

        res.saturation_snapshots = sat_snaps
        res.pressure_snapshots = pres_snaps
        res.n_steps = step
        res.wall_time = timer.perf_counter() - t_wall_start
        res.pore_volumes_injected = res.cum_injected[-1] / total_pv_bbl
        res.compute_kpis()

        if verbose:
            print(f"\nDone: {step} steps, {res.wall_time:.2f} s wall time\n")

        return res

    # ---- Console output helpers ----
    @staticmethod
    def _print_header():
        print(f"\n{'Step':>7} {'Time':>10} {'dt':>8} {'Oil Rate':>10} "
              f"{'WCut%':>8} {'CumOil':>12} {'RF%':>8}")
        print("-" * 72)

    @staticmethod
    def _print_row(step, time, dt, metrics, cum_o, rf):
        print(f"{step:7d} {time:10.1f} {dt:8.4f} "
              f"{metrics['q_oil_surf']:10.1f} "
              f"{metrics['water_cut'] * 100:8.2f} "
              f"{cum_o:12.0f} {rf:8.2f}")
