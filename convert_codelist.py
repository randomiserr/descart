import pandas as pd
import json
import os
import re

SOURCE_FILE = r"C:\Users\ccaal\Downloads\projects\Descart\Gathered data\TECH\budget-item_26-11-2025.xlsx"
OUTPUT_FILE = r"C:\Users\ccaal\Downloads\projects\Descart\data\codelists\items.json"

def convert():
    print(f"Reading {SOURCE_FILE}...")
    
    # Read without header first to find the real header
    df = pd.read_excel(SOURCE_FILE, header=None)
    
    # Find header row
    header_idx = -1
    for i, row in df.iterrows():
        row_str = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
        if "kód" in row_str and "název" in row_str:
            header_idx = i
            break
            
    if header_idx == -1:
        # Fallback: maybe it's "Code" and "Name"
        for i, row in df.iterrows():
            row_str = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
            if "code" in row_str and "name" in row_str:
                header_idx = i
                break
    
    if header_idx == -1:
        print("Could not find header row with 'Kód'/'Code' and 'Název'/'Name'.")
        # Let's assume row 0 or 1 if not found, or print columns to debug
        # But let's try to just look for the first row with 2+ strings?
        # Actually, let's just try to read with header=0 and see if we can map columns by index
        # Assuming Col 0 is Code, Col 1 is Name (or similar)
        print("Assuming header is at row 0 or data starts there...")
        df = pd.read_excel(SOURCE_FILE)
    else:
        print(f"Found header at row {header_idx}")
        df = pd.read_excel(SOURCE_FILE, header=header_idx)

    # Identify Code and Name columns
    code_col = None
    name_col = None
    
    for col in df.columns:
        c = str(col).lower()
        if "kód" in c or "code" in c:
            code_col = col
        if "název" in c or "name" in c:
            name_col = col
            
    if not code_col or not name_col:
        print(f"Could not identify columns. Found: {df.columns.tolist()}")
        # Fallback to index 0 and 1?
        if len(df.columns) >= 2:
            code_col = df.columns[0]
            name_col = df.columns[1]
            print(f"Falling back to index 0 ({code_col}) and 1 ({name_col})")
        else:
            return

    print(f"Using Code='{code_col}', Name='{name_col}'")
    
    mapping = {}
    for _, row in df.iterrows():
        try:
            raw_code = str(row[code_col])
            name = str(row[name_col])
            
            if pd.isna(raw_code) or pd.isna(name):
                continue
                
            # Clean code: remove commas, dots, spaces
            # User said "1,111" -> "1111"
            clean_code = re.sub(r'[,\.\s]', '', raw_code)
            
            # Ensure it's 4 digits if it's a budget item (usually 4)
            # But chapters are 3. Let's just store what we have.
            
            mapping[clean_code] = name.strip()
        except Exception:
            continue
            
    print(f"Extracted {len(mapping)} items.")
    
    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    convert()
