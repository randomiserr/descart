import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BUDGET_PATH = os.path.join(DATA_DIR, 'budget_2025.csv')

def inspect_csv():
    if not os.path.exists(BUDGET_PATH):
        print("Budget file not found.")
        return

    try:
        with open(BUDGET_PATH, 'r', encoding='utf-8-sig') as f:
            # Force semicolon delimiter
            reader = csv.reader(f, delimiter=';')
            headers = next(reader)
            
            print(f"Headers ({len(headers)}):")
            for i, h in enumerate(headers):
                print(f"  {i}: {h}")
            
            print("\nFirst 5 rows:")
            for i, row in enumerate(reader):
                if i >= 5: break
                print(f"Row {i}: {row}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_csv()
