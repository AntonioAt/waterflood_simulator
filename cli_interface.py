"""
cli_interface.py
----------------
Command-Line Interface for the Waterflood Simulator.
Handles user inputs, template generation, and Excel/JSON parsing.
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
        # Sheet 1: Global_Params
        df_global = pd.DataFrame({
            'Group': ['wells', 'wells', 'total_time', 'rock', 'rock'],
            'Parameter': ['q_inj', 'mode', 'value', 'nx', 'permeability'],
            'Value': [500.0, 'rate', 2000.0, 100, 100.0]
        })
        df_global.to_excel(writer, sheet_name='Global_Params', index=False)
        
        # Sheet 2: RelPerm_SCAL
        df_scal = pd.DataFrame({
            'Sw': [0.2, 0.4, 0.6, 0.8],
            'krw': [0.0, 0.1, 0.4, 1.0],
            'kro': [1.0, 0.5, 0.1, 0.0]
        })
        df_scal.to_excel(writer, sheet_name='RelPerm_SCAL', index=False)
        
        # Sheet 3: Rock_Arrays
        # Generating a dummy array matching nx=100
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
    Includes rigorous error handling and data validation.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Critical Error: Cannot find the file '{filepath}'.")

    print(f"\n[INFO] Loading Excel configuration from: {filepath}")
    cfg = SimulationConfig()

    try:
        # --- 1. Parse Global Parameters ---
        print("  -> Parsing 'Global_Params' sheet...")
        df_global = pd.read_excel(filepath, sheet_name='Global_Params')
        
        for index, row in df_global.iterrows():
            # Clean string inputs to prevent whitespace errors
            group = str(row['Group']).strip()
            param = str(row['Parameter']).strip()
            val = row['Value']

            # Dynamic attribute mapping
            if hasattr(cfg, group):
                group_obj = getattr(cfg, group)
                if hasattr(group_obj, param):
                    setattr(group_obj, param, val)
            elif hasattr(cfg, param): # For top-level attributes like total_time
                setattr(cfg, param, val)

        # --- 2. Parse Relative Permeability (SCAL) ---
        try:
            df_scal = pd.read_excel(filepath, sheet_name='RelPerm_SCAL')
            # Extract to temporary CSV so the existing RelPerm class can read it
            temp_csv = "temp_relperm_from_excel.csv"
            df_scal.to_csv(temp_csv, index=False)
            cfg.relperm.csv_filepath = temp_csv
            print("  -> [OK] SCAL table loaded successfully.")
        except ValueError:
            print("  -> [WARN] No 'RelPerm_SCAL' sheet found. Using default Corey models.")

        # --- 3. Parse Rock Arrays (Heterogeneity) ---
        try:
            df_rock = pd.read_excel(filepath, sheet_name='Rock_Arrays')
            # Clean column names in case user added spaces
            df_rock.columns = df_rock.columns.str.strip()
            
            if 'Permeability_mD' in df_rock.columns:
                perm_array = df_rock['Permeability_mD'].values
                
                # Rigorous validation: Check matrix dimension
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


def main_menu() -> SimulationConfig:
    """Displays the interactive CLI menu and routes the user choice."""
    print("=" * 60)
    print("  WATERFLOOD SIMULATOR - INITIALIZATION MENU")
    print("=" * 60)
    print("  1. Run with default parameters (Base Case)")
    print("  2. Load configuration from JSON")
    print("  3. Load full deck from Excel (.xlsx)")
    print("  4. Generate example templates (Excel & JSON)")
    print("  0. Exit")
    print("=" * 60)
    
    choice = input("Enter your choice (0-4): ").strip()

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
        
    elif choice == '0':
        print("Exiting simulator...")
        sys.exit(0)
        
    else:
        print("\n[ERROR] Invalid choice. Initializing with default parameters...")
        return SimulationConfig()


if __name__ == "__main__":
    # Test the menu visually
    config = main_menu()
    print("\n--- Final Configuration Check ---")
    print(f"Grid nx: {config.rock.nx}")
    print(f"Injection Rate: {config.wells.q_inj} bbl/day")
    print(f"Simulation Time: {config.total_time} days")
