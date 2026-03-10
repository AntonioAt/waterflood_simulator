"""
simulator.py
============
Core simulation engine — the WaterfloodSimulator class.
Attaches to main via: from simulator import WaterfloodSimulator
"""

import numpy as np
import time as timer

from config import SimulationConfig
from grid import Grid
from relperm import RelativePermeability
from capillary import CapillaryPressure
from flow import FlowCalculator
from saturation import SaturationUpdater
from pressure_solver import PressureSolver
from production import ProductionCalculator
from results import SimulationResults


class WaterfloodSimulator:
    """1-D two-phase waterflood simulator."""

    def __init__(self, config: SimulationConfig = None):
        self.cfg = config if config is not None else SimulationConfig()
        self._setup()

    def _setup(self):
        """Instantiate sub-modules."""
        self.grid = Grid(self.cfg.rock)
        self.relperm = RelativePermeability(self.cfg.relperm)
        self.cap_press = CapillaryPressure(
            self.cfg.capillary, self.cfg.relperm
        )
        self.flow_calc = FlowCalculator(
            self.cfg, self.relperm, self.cap_press
        )
        self.sat_updater = SaturationUpdater(
            self.grid, self.cfg, self.flow_calc
        )
        self.pressure_solver = PressureSolver(self.grid, self.cfg)
        self.prod_calc = ProductionCalculator(self.cfg, self.flow_calc)

    def run(self, verbose: bool = True) -> SimulationResults:
        """Execute the simulation."""
        t_start = timer.perf_counter()

        nx = self.grid.nx
        cfg = self.cfg

        # Initialise state
        Sw = np.full(nx, cfg.Sw_init)
        pressure = np.full(nx, cfg.wells.p_init)

        # Volumetrics
        pv = self.grid.porosity * self.grid.area * self.grid.dx
        total_pv = pv * nx
        ft3_to_bbl = 0.178107
        total_pv_bbl = total_pv * ft3_to_bbl
        ooip = total_pv_bbl * (1.0 - cfg.Sw_init) / cfg.fluid.Bo

        # Results container
        res = SimulationResults()
        res.x = self.grid.x.copy()
        res.perm_field = self.grid.perm.copy()
        res.config = cfg

        # Initial record
        q_total = cfg.wells.q_inj
        res.times.append(0.0)
        res.dt_history.append(0.0)
        res.oil_rate.append(q_total / cfg.fluid.Bo)
        res.water_rate.append(0.0)
        res.water_cut.append(0.0)
        res.cum_oil.append(0.0)
        res.cum_water.append(0.0)
        res.cum_injected.append(0.0)
        res.avg_pressure.append(cfg.wells.p_init)
        res.avg_Sw.append(cfg.Sw_init)
        res.recovery_factor.append(0.0)

        # Snapshot schedule
        n_snaps = 8
        snap_times = np.linspace(0, cfg.total_time, n_snaps + 1)[1:]
        snap_idx = 0

        # Time loop
        sim_time = 0.0
        step = 0
        dt_target = cfg.numerical.dt_init

        if verbose:
            print(
                f"{'Step':>7} {'Time':>10} {'dt':>8} {'Oil Rate':>10} "
                f"{'WCut%':>8} {'CumOil':>12} {'RF%':>8}"
            )
            print("-" * 75)

        while sim_time < cfg.total_time:
            # Determine injection rate
            if cfg.wells.mode == "pressure":
                _, lam_t = self.flow_calc.fractional_flow(Sw)
                pressure, q_total = self.pressure_solver.solve(
                    Sw, lam_t
                )
                q_total = max(q_total, 0.0)
            else:
                q_total = cfg.wells.q_inj

            # Adaptive time step
            dt = self.sat_updater.adaptive_dt(Sw, q_total, dt_target)
            if sim_time + dt > cfg.total_time:
                dt = cfg.total_time - sim_time

            # Update saturation
            Sw_new = self.sat_updater.update(Sw, q_total, dt)

            # Limit max saturation change (cut dt if needed)
            max_change = np.max(np.abs(Sw_new - Sw))
            if (max_change > cfg.numerical.max_dSw_per_step
                    and dt > cfg.numerical.dt_min):
                scale = cfg.numerical.max_dSw_per_step / (
                    max_change + 1e-30
                )
                dt *= scale
                Sw_new = self.sat_updater.update(Sw, q_total, dt)

            Sw = Sw_new
            sim_time += dt
            step += 1

            # Production
            metrics = self.prod_calc.compute(Sw, q_total, pressure)

            cum_o = (res.cum_oil[-1]
                     + 0.5 * (res.oil_rate[-1]
                              + metrics["q_oil_surf"]) * dt)
            cum_w = (res.cum_water[-1]
                     + 0.5 * (res.water_rate[-1]
                              + metrics["q_water_surf"]) * dt)
            cum_inj = res.cum_injected[-1] + q_total * dt
            rf = cum_o / ooip * 100.0 if ooip > 0 else 0.0

            # Store
            res.times.append(sim_time)
            res.dt_history.append(dt)
            res.oil_rate.append(metrics["q_oil_surf"])
            res.water_rate.append(metrics["q_water_surf"])
            res.water_cut.append(metrics["water_cut"])
            res.cum_oil.append(cum_o)
            res.cum_water.append(cum_w)
            res.cum_injected.append(cum_inj)
            res.avg_pressure.append(metrics["avg_pressure"])
            res.avg_Sw.append(metrics["avg_Sw"])
            res.recovery_factor.append(rf)

            # Snapshots
            if (snap_idx < len(snap_times)
                    and sim_time >= snap_times[snap_idx]):
                label = f"t = {snap_times[snap_idx]:.0f} d"
                res.saturation_snapshots[label] = Sw.copy()
                res.pressure_snapshots[label] = pressure.copy()
                snap_idx += 1

            # Print progress
            if verbose and (
                step % max(1, int(cfg.total_time / dt / 20)) == 0
                or sim_time >= cfg.total_time
            ):
                print(
                    f"{step:7d} {sim_time:10.1f} {dt:8.3f} "
                    f"{metrics['q_oil_surf']:10.1f} "
                    f"{metrics['water_cut'] * 100:8.2f} "
                    f"{cum_o:12.0f} {rf:8.2f}"
                )

            # Gradually try to increase dt
            dt_target = min(dt * 1.1, cfg.numerical.dt_max)

        # Final snapshot
        res.saturation_snapshots["Final"] = Sw.copy()
        res.pressure_snapshots["Final"] = pressure.copy()

        # Post-process: convert lists to arrays
        res.times = np.array(res.times)
        res.dt_history = np.array(res.dt_history)
        res.oil_rate = np.array(res.oil_rate)
        res.water_rate = np.array(res.water_rate)
        res.water_cut = np.array(res.water_cut)
        res.cum_oil = np.array(res.cum_oil)
        res.cum_water = np.array(res.cum_water)
        res.cum_injected = np.array(res.cum_injected)
        res.avg_pressure = np.array(res.avg_pressure)
        res.avg_Sw = np.array(res.avg_Sw)
        res.recovery_factor = np.array(res.recovery_factor)
        res.n_steps = step
        res.wall_time = timer.perf_counter() - t_start
        res.pore_volumes_injected = res.cum_injected[-1] / total_pv_bbl
        res.final_recovery = res.recovery_factor[-1]

        # Breakthrough time
        bt_mask = res.water_cut > 0.01
        res.breakthrough_time = (
            res.times[bt_mask][0] if np.any(bt_mask) else np.nan
        )

        if verbose:
            print(
                f"\nSimulation complete: {step} steps in "
                f"{res.wall_time:.2f} s"
            )

        return res