"""
cli_interface.py
----------------
Command-Line Interface for the Waterflood Simulator.
Handles interactive user inputs, template generation, and external data parsing.
"""

import os
import sys
import pandas as pd
import json
from config import SimulationConfig


def generate_templates():
    """Generates standard template files for user input."""
    print("\n--- Generating Template Files ---")
    
    # 1. JSON Template
    json_template = {
        "total_time": 1500.0,
        "rock": {"permeability": 150.0, "porosity": 0.22},
        "wells": {"q_inj": 600.0, "mode": "rate"}
    }
    with open("example_input.json", "w") as f:
        json.dump(json_template, f, indent=4)
    print("  [OK] Created: example_input.json")

    # 2. Excel Template (Multi-sheet)
    excel_filename = 'example_full_deck.xlsx'
    with pd.ExcelWriter(excel_filename) as writer:
        # Sheet 1: Global parameters mapped dynamically
        df_global = pd.DataFrame({
            'Group': ['wells', 'wells', 'total_time', 'rock', 'rock'],
            'Parameter': ['q_inj', 'mode', 'value', 'nx', 'permeability'],
            'Value': [500.0, 'rate', 2000.0, 100, 100.0]
        })
        df_global.to_excel(writer, sheet_name='Global_Params', index=False)
        
        # Sheet 2: Tabular relative permeability data
        df_scal = pd.DataFrame({
            'Sw': [0.2, 0.4, 0.6, 0.8],
            'krw': [0.0, 0.1, 0.4, 1.0],
            'kro': [1.0, 0.5, 0.1, 0.0]
        })
        df_scal.to_excel(writer, sheet_name='RelPerm_SCAL', index=False)
        
        # Sheet 3: Spatial rock heterogeneity array
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
    """
    Parses a multi-sheet Excel file into a SimulationConfig object.
    Implements rigorous validation to prevent matrix dimension mismatches.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Critical Error: Cannot find the file '{filepath}'.")

    print(f"\n[INFO] Loading Excel configuration from: {filepath}")
    cfg = SimulationConfig()

    try:
        # --- Parse Global Parameters ---
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

        # --- Parse Relative Permeability (SCAL) ---
        try:
            df_scal = pd.read_excel(filepath, sheet_name='RelPerm_SCAL')
            temp_csv = "temp_relperm_from_excel.csv"
            df_scal.to_csv(temp_csv, index=False)
            cfg.relperm.csv_filepath = temp_csv
            print("  -> [OK] SCAL table loaded successfully.")
        except ValueError:
            print("  -> [WARN] No 'RelPerm_SCAL' sheet found. Using default Corey models.")

        # --- Parse Rock Arrays (Heterogeneity) ---
        try:
            df_rock = pd.read_excel(filepath, sheet_name='Rock_Arrays')
            df_rock.columns = df_rock.columns.str.strip()
            
            if 'Permeability_mD' in df_rock.columns:
                perm_array = df_rock['Permeability_mD'].values
                if len(perm_array) == cfg.rock.nx:
                    cfg.rock.perm_array = perm_array
                    print(f"  -> [OK] Rock permeability array loaded (nx={len(perm_array)}).")
                else:
                    print(f"  -> [ERROR] Dimension mismatch! Excel array length ({len(perm_array)}) "
                          f"does not match grid nx ({cfg.rock.nx}). Falling back to uniform permeability.")
        except ValueError:
            print("  -> [WARN] No 'Rock_Arrays' sheet found. Using uniform rock properties.")

        return cfg

    except Exception as e:
        raise RuntimeError(f"Failed to parse Excel file. Details: {e}")


def get_manual_config() -> SimulationConfig:
    """
    Prompts the user for key simulation parameters interactively via CLI.
    Limits inputs to essential parameters to minimize parsing errors.
    """
    cfg = SimulationConfig()
    print("\n" + "-" * 40)
    print("  MANUAL PARAMETER INPUT")
    print("-" * 40)
    print("Instruction: Press 'Enter' without typing to use the default value.\n")

    try:
        perm_in = input(f"Rock Permeability (mD) [Default: {cfg.rock.permeability}]: ").strip()
        if perm_in: cfg.rock.permeability = float(perm_in)

        poro_in = input(f"Rock Porosity (fraction) [Default: {cfg.rock.porosity}]: ").strip()
        if poro_in: cfg.rock.porosity = float(poro_in)

        q_inj_in = input(f"Water Injection Rate (bbl/day) [Default: {cfg.wells.q_inj}]: ").strip()
        if q_inj_in: cfg.wells.q_inj = float(q_inj_in)

        time_in = input(f"Total Simulation Time (days) [Default: {cfg.total_time}]: ").strip()
        if time_in: cfg.total_time = float(time_in)

    except ValueError:
        print("\n[!] WARNING: Invalid numeric input detected.")
        print("[!] The simulator will ignore the invalid input and use defaults for the remaining parameters.")

    return cfg


def main_menu() -> SimulationConfig:
    """Displays the interactive CLI menu and routes the user's operational choice."""
    print("=" * 60)
    print("  WATERFLOOD SIMULATOR - INITIALIZATION MENU")
    print("=" * 60)
    print("  1. Run with default parameters (Base Case)")
    print("  2. Load configuration from JSON")
    print("  3. Load full deck from Excel (.xlsx)")
    print("  4. Generate example templates (Excel & JSON)")
    print("  5. Manual CLI Input (Basic Parameters)")
    print("  0. Exit")
    print("=" * 60)
    
    choice = input("Enter your choice (0-5): ").strip()

    if choice == '1':
        print("\n[INFO] Initializing with default parameters...")
        return SimulationConfig()
        
    elif choice == '2':
        filepath = input("Enter the JSON filename (e.g., input.json): ").strip()
        try:
            return SimulationConfig.from_json(filepath)
        except Exception as e:
            print(f"\n[ERROR] Failed to load JSON: {e}")
            sys.exit(1)
            
    elif choice == '3':
        filepath = input("Enter the Excel filename (e.g., data.xlsx): ").strip()
        try:
            return load_excel_deck(filepath)
        except Exception as e:
            print(f"\n[ERROR] Failed to load Excel: {e}")
            sys.exit(1)
            
    elif choice == '4':
        generate_templates()
        print("\n[INFO] Templates generated. Please edit them and run the program again.")
        sys.exit(0)

    elif choice == '5':
        return get_manual_config()
        
    elif choice == '0':
        print("Exiting simulator...")
        sys.exit(0)
        
    else:
        print("\n[ERROR] Invalid choice. Initializing with default parameters...")
        return SimulationConfig()
