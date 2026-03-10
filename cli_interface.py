"""
cli_interface.py
----------------
Command-Line Interface for the Waterflood Simulator.
Initializes the base configuration, handles external file parsing, and routes the execution pipeline.
"""

import os
import sys
import pandas as pd
import json
from typing import Tuple
from config import SimulationConfig


def generate_templates():
    """Generates standard template files demonstrating how to override base parameters and bounds."""
    print("\n--- Generating Template Files ---")
    
    json_template = {
        "total_time": 1500.0,
        "rock": {"permeability": 150.0, "porosity": 0.22},
        "bounds": {
            "q_inj_min_mult": 0.25, 
            "unfav_mu_o": 15.0,
            "channel_high_mult": 10.0
        } 
    }
    with open("example_input.json", "w") as f:
        json.dump(json_template, f, indent=4)
    print("  [OK] Created: example_input.json")

    excel_filename = 'example_full_deck.xlsx'
    with pd.ExcelWriter(excel_filename) as writer:
        df_global = pd.DataFrame({
            'Group': ['wells', 'rock', 'bounds', 'bounds', 'bounds'],
            'Parameter': ['q_inj', 'permeability', 'q_inj_min_mult', 'unfav_mu_o', 'channel_high_mult'],
            'Value': [500.0, 100.0, 0.25, 12.0, 8.0]
        })
        df_global.to_excel(writer, sheet_name='Global_Params', index=False)
        
        df_scal = pd.DataFrame({
            'Sw': [0.2, 0.4, 0.6, 0.8],
            'krw': [0.0, 0.1, 0.4, 1.0],
            'kro': [1.0, 0.5, 0.1, 0.0]
        })
        df_scal.to_excel(writer, sheet_name='RelPerm_SCAL', index=False)
        
        df_rock = pd.DataFrame({
            'Grid_Index': range(100),
            'Depth_ft': [5000 + (i * 10) for i in range(100)],
            'Permeability_mD': [100.0] * 100,
            'Porosity_frac': [0.20] * 100
        })
        df_rock.to_excel(writer, sheet_name='Rock_Arrays', index=False)
        
    print(f"  [OK] Created: {excel_filename}")
    print("-" * 33)


def load_excel_deck(filepath: str) -> SimulationConfig:
    """Parses a multi-sheet Excel file into a SimulationConfig object."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Critical Error: Cannot find the file '{filepath}'.")

    print(f"\n[INFO] Loading Excel configuration from: {filepath}")
    cfg = SimulationConfig()

    try:
        print("  -> Parsing 'Global_Params' sheet...")
        df_global = pd.read_excel(filepath, sheet_name='Global_Params')
        for index, row in df_global.iterrows():
            group = str(row['Group']).strip()
            param = str(row['Parameter']).strip()
            val = row['Value']

            if hasattr(cfg, group):
                group_obj = getattr(cfg, group)
                if hasattr(group_obj, param):
                    setattr(group_obj, param, val)
            elif hasattr(cfg, param):
                setattr(cfg, param, val)

        try:
            df_scal = pd.read_excel(filepath, sheet_name='RelPerm_SCAL')
            temp_csv = "temp_relperm_from_excel.csv"
            df_scal.to_csv(temp_csv, index=False)
            cfg.relperm.csv_filepath = temp_csv
            print("  -> [OK] SCAL table loaded successfully.")
        except ValueError:
            print("  -> [WARN] No 'RelPerm_SCAL' sheet found.")

        try:
            df_rock = pd.read_excel(filepath, sheet_name='Rock_Arrays')
            df_rock.columns = df_rock.columns.str.strip()
            
            if 'Permeability_mD' in df_rock.columns:
                perm_array = df_rock['Permeability_mD'].values
                if len(perm_array) == cfg.rock.nx:
                    cfg.rock.perm_array = perm_array
                    print(f"  -> [OK] Rock permeability array loaded (nx={len(perm_array)}).")
                else:
                    print("  -> [ERROR] Dimension mismatch! Falling back to uniform permeability.")
        except ValueError:
            print("  -> [WARN] No 'Rock_Arrays' sheet found.")

        return cfg

    except Exception as e:
        raise RuntimeError(f"Failed to parse Excel file. Details: {e}")


def get_manual_config() -> SimulationConfig:
    """Prompts the user for key simulation parameters and boundaries interactively."""
    cfg = SimulationConfig()
    print("\n" + "-" * 60)
    print("  MANUAL PARAMETER INPUT")
    print("-" * 60)
    print("Instruction: Press 'Enter' without typing to use the default value.\n")

    try:
        # --- 1. Base Parameters ---
        print("--- BASE CASE PARAMETERS ---")
        perm_in = input(f"Rock Permeability (mD) [Default: {cfg.rock.permeability}]: ").strip()
        if perm_in: cfg.rock.permeability = float(perm_in)

        time_in = input(f"Total Simulation Time (days) [Default: {cfg.total_time}]: ").strip()
        if time_in: cfg.total_time = float(time_in)

        # --- 2. Sensitivity Bounds ---
        print("\n--- SENSITIVITY BOUNDS (MIN/MAX) ---")
        q_min = input(f"Min Injection Rate Multiplier [Default: {cfg.bounds.q_inj_min_mult}]: ").strip()
        if q_min: cfg.bounds.q_inj_min_mult = float(q_min)
        
        q_max = input(f"Max Injection Rate Multiplier [Default: {cfg.bounds.q_inj_max_mult}]: ").strip()
        if q_max: cfg.bounds.q_inj_max_mult = float(q_max)

        # --- 3. Scenario Comparison Bounds ---
        print("\n--- SCENARIO COMPARISON INPUTS ---")
        fav_o = input(f"Favorable Scenario Oil Viscosity (cp) [Default: {cfg.bounds.fav_mu_o}]: ").strip()
        if fav_o: cfg.bounds.fav_mu_o = float(fav_o)
        
        unfav_o = input(f"Unfavorable Scenario Oil Viscosity (cp) [Default: {cfg.bounds.unfav_mu_o}]: ").strip()
        if unfav_o: cfg.bounds.unfav_mu_o = float(unfav_o)

        ch_high = input(f"Channel Scenario High-Perm Multiplier [Default: {cfg.bounds.channel_high_mult}]: ").strip()
        if ch_high: cfg.bounds.channel_high_mult = float(ch_high)

    except ValueError:
        print("\n[!] WARNING: Invalid numeric input detected. Using defaults for the remaining parameters.")

    return cfg


def initialize_base_config() -> SimulationConfig:
    """Handles the first stage of CLI routing to establish the base configuration."""
    print("=" * 60)
    print("  STEP 1: INITIALIZE BASE CONFIGURATION")
    print("=" * 60)
    print("  1. Standard Default Base Case")
    print("  2. Load from JSON")
    print("  3. Load from Excel (.xlsx)")
    print("  4. Manual CLI Input")
    print("  5. Generate Template Files (Excel & JSON)")
    print("  0. Exit")
    print("=" * 60)
    
    choice = input("Select base configuration method (0-5): ").strip()

    if choice == '1':
        return SimulationConfig()
    elif choice == '2':
        filepath = input("Enter JSON filename: ").strip()
        return SimulationConfig.from_json(filepath)
    elif choice == '3':
        filepath = input("Enter Excel filename: ").strip()
        return load_excel_deck(filepath)
    elif choice == '4':
        return get_manual_config()
    elif choice == '5':
        generate_templates()
        sys.exit(0)
    elif choice == '0':
        sys.exit(0)
    else:
        return SimulationConfig()


def select_execution_mode() -> str:
    """Handles the second stage of CLI routing to define the simulation action."""
    print("\n" + "=" * 60)
    print("  STEP 2: SELECT EXECUTION MODE")
    print("=" * 60)
    print("  1. Run Single Simulation (Evaluate Base Case only)")
    print("  2. Run Scenario Comparison")
    print("  3. Run Parametric Sensitivity Analysis (Min/Base/Max)")
    print("  4. AUTO-GENERATE ALL OUTPUTS (Runs 1, 2, and 3 sequentially)")
    print("=" * 60)
    
    choice = input("Select execution mode (1-4): ").strip()
    
    if choice == '2': return "scenario"
    elif choice == '3': return "sensitivity"
    elif choice == '4': return "all"
    else: return "single"


def main_menu() -> Tuple[str, SimulationConfig]:
    """Orchestrates the CLI flow."""
    config = initialize_base_config()
    action = select_execution_mode()
    return action, config
