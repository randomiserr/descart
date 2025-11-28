import os
import requests
import zipfile
import io
import datetime

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
BUDGET_CSV_PATH = os.path.join(DATA_DIR, 'budget_2025.csv')

# URL Pattern for Monitor Open Data (FinOSS - State Budget)
# https://monitor.statnipokladna.gov.cz/data/extrakty/csv/FinOSS/2025_09_Data_CSUIS_MISRIS.zip
BASE_URL = "https://monitor.statnipokladna.gov.cz/data/extrakty/csv/FinOSS"

def download_latest_budget():
    """
    Attempts to download the latest available monthly budget export.
    """
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    # Try current month, then previous months
    today = datetime.date.today()
    
    # Try going back up to 3 months
    for i in range(4):
        # Calculate target date
        target_date = today - datetime.timedelta(days=30 * i)
        year = target_date.year
        month = target_date.month
        
        filename = f"{year}_{month:02d}_Data_CSUIS_MISRIS.zip"
        url = f"{BASE_URL}/{filename}"
        
        print(f"Trying to download: {url}...")
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Download successful!")
                process_zip(response.content)
                return
            else:
                print(f"Not found (Status {response.status_code})")
        except Exception as e:
            print(f"Error: {e}")

    print("Could not find any recent budget data.")

def process_zip(zip_content):
    """
    Extracts the ZIP and saves the main CSV.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            # List files
            print("Files in ZIP:", z.namelist())
            
            # Find the main data CSV (usually larger file or specific name)
            # The naming convention inside might vary, so we take the largest CSV
            csv_files = [f for f in z.namelist() if f.lower().endswith('.csv')]
            
            if not csv_files:
                print("No CSV found in ZIP.")
                return

            # Sort by size, largest first (assuming it's the data, not metadata)
            csv_files.sort(key=lambda x: z.getinfo(x).file_size, reverse=True)
            target_file = csv_files[0]
            
            print(f"Extracting {target_file} to {BUDGET_CSV_PATH}...")
            
            with z.open(target_file) as source, open(BUDGET_CSV_PATH, 'wb') as target:
                target.write(source.read())
            
            print("Done.")
            
    except Exception as e:
        print(f"Failed to process ZIP: {e}")

if __name__ == "__main__":
    download_latest_budget()
