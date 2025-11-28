import requests
import json
import os
import datetime

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MACRO_JSON_PATH = os.path.join(DATA_DIR, 'macro_real.json')

# Dataset IDs
DATASETS = {
    "GDP": "NUC06QT01",
    "Inflation": "CEN0101HT01", 
    "Unemployment": "ZAM05T1"
}

BASE_API = "https://data.csu.gov.cz/api/katalog/v1/sady"

def get_dataset_url(dataset_id):
    """
    Fetches metadata to find the CSV download URL.
    """
    url = f"{BASE_API}/{dataset_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        meta = resp.json()
        
        # Look for 'zdroje' (resources)
        resources = meta.get('zdroje', [])
        for res in resources:
            if 'csv' in res.get('format', '').lower():
                return res.get('url')
        
        # Fallback: try to construct it if standard pattern exists
        # (The docs mentioned /data/sady/{id}/csv or similar, but let's rely on metadata first)
        return None
    except Exception as e:
        print(f"Error getting metadata for {dataset_id}: {e}")
        return None

def download_and_parse_macro():
    results = []
    
    for name, ds_id in DATASETS.items():
        print(f"Processing {name} ({ds_id})...")
        
        # 1. Get Metadata
        # Note: The API might be slightly different, let's try a direct data query if catalog fails
        # Actually, let's try a direct JSON-STAT or CSV endpoint which is common for CSU
        # Pattern: https://data.csu.gov.cz/api/v2/sady/{id}/data (Guessing v2 based on other open data portals)
        
        # Let's try the catalog approach first
        csv_url = get_dataset_url(ds_id)
        
        if not csv_url:
            # Fallback to a known pattern if metadata doesn't have it
            # https://www.czso.cz/documents/10180/183398098/NUC06QT01.csv (Example pattern)
            # But let's try to just use the ID in the 'vyber' URL pattern we saw
            print(f"  Could not find CSV URL in metadata for {ds_id}")
            continue
            
        print(f"  Downloading CSV from {csv_url}...")
        try:
            resp = requests.get(csv_url)
            resp.raise_for_status()
            lines = resp.text.splitlines()
            
            # PARSING LOGIC (Naive, assumes latest is at bottom or top)
            # We need to inspect the CSV structure. 
            # For now, we'll just save the raw CSV to a file and let the Tool Layer parse it on demand?
            # No, we want to update 'macro_real.json' with a snapshot.
            
            # Let's save the raw CSV first to debug
            with open(os.path.join(DATA_DIR, f"{ds_id}.csv"), 'w', encoding='utf-8') as f:
                f.write(resp.text)
                
            # Naive parsing: take the last line
            if len(lines) > 1:
                last_line = lines[-1]
                parts = last_line.split(',')
                # This is risky without knowing columns.
                # Let's just store that we have the file.
                
                results.append({
                    "indicator": name,
                    "source_file": f"{ds_id}.csv",
                    "dataset_id": ds_id,
                    "last_updated": str(datetime.date.today())
                })
                
        except Exception as e:
            print(f"  Failed to download/parse: {e}")

    # Save index
    with open(MACRO_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Saved macro index to {MACRO_JSON_PATH}")

if __name__ == "__main__":
    download_and_parse_macro()
