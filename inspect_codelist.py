import os
import sys

def inspect_excel():
    file_path = r"C:\Users\ccaal\Downloads\projects\Descart\Gathered data\TECH\budget-item_26-11-2025.xlsx"
    
    print(f"Inspecting {file_path}...")
    
    try:
        import pandas as pd
        
        # Read the Excel file
        # Sometimes headers are not on row 0
        df = pd.read_excel(file_path, header=None)
        
        print(f"\nShape: {df.shape}")
        
        print("\nFirst 10 rows (raw):")
        print(df.head(10).to_string())
        
        # Try to find the header row
        # Look for a row that contains "Code" or "Kód" or "Položka"
        header_row_idx = -1
        for i, row in df.iterrows():
            row_str = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
            if "kód" in row_str or "code" in row_str or "položka" in row_str:
                header_row_idx = i
                print(f"\nPotential header found at row {i}: {row.tolist()}")
                break
        
        if header_row_idx != -1:
            df = pd.read_excel(file_path, header=header_row_idx)
            print("\nReloaded with header:")
            print(df.columns.tolist())
            print(df.head().to_string())
            
    except ImportError:
        print("Error: pandas or openpyxl not installed. Please run: pip install pandas openpyxl")
    except Exception as e:
        print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    inspect_excel()
