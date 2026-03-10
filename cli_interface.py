def get_manual_config() -> SimulationConfig:
    """
    Prompts the user for key simulation parameters interactively via CLI.
    Limits inputs to a few essential parameters to minimize human error.
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
    """Displays the interactive CLI menu and routes the user choice."""
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
            import sys; sys.exit(1)
            
    elif choice == '3':
        filepath = input("Enter the Excel filename (e.g., data.xlsx): ").strip()
        try:
            return load_excel_deck(filepath) # Assumes you have this function from the previous code
        except Exception as e:
            print(f"\n[ERROR] Failed to load Excel: {e}")
            import sys; sys.exit(1)
            
    elif choice == '4':
        generate_templates() # Assumes you have this function from the previous code
        print("\n[INFO] Templates generated. Please edit them and run the program again.")
        import sys; sys.exit(0)

    elif choice == '5':
        return get_manual_config()
        
    elif choice == '0':
        print("Exiting simulator...")
        import sys; sys.exit(0)
        
    else:
        print("\n[ERROR] Invalid choice. Initializing with default parameters...")
        return SimulationConfig()
