import os
import subprocess
import sys

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    try:
        subprocess.run([sys.executable, script_name], check=True)
        print(f"--- {script_name} completed successfully ---\n")
    except subprocess.CalledProcessError as e:
        print(f"!!! {script_name} failed with error: {e} !!!\n")

def main():
    print("=== Starting Data Update ===\n")
    
    # 1. Macro Data (Fastest)
    run_script("download_macro.py")
    
    # 2. Budget Data (Slower download)
    run_script("download_budget.py")
    
    # 3. Laws Ingestion (Local processing)
    # Only run if there are new files in raw, but safe to rerun
    run_script("ingest_data.py")
    
    print("=== Data Update Complete ===")
    print("You are now ready to run 'main.py'.")

if __name__ == "__main__":
    main()
