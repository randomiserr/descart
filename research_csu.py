import requests
import json

CATALOG_URL = "https://data.csu.gov.cz/api/katalog/v1/sady"

def search_datasets():
    print(f"Fetching datasets from {CATALOG_URL}...")
    try:
        response = requests.get(CATALOG_URL)
        response.raise_for_status()
        datasets = response.json()
        print(f"Found {len(datasets)} datasets.")
        
        keywords = {
            "GDP": ["HDP", "hrubý domácí produkt"],
            "Inflation": ["inflace", "spotřebitelských cen"],
            "Unemployment": ["nezaměstnanost"],
            "Wages": ["mzdy", "průměrná mzda"]
        }
        
        found = {k: [] for k in keywords}
        
        for ds in datasets:
            # The API structure might vary, let's inspect the first one if we fail
            # Assuming 'kod' and 'nazev' or similar fields
            code = ds.get('kod', '') or ds.get('id', '')
            name = ds.get('nazev', '') or ds.get('name', '')
            
            text_to_search = (code + " " + name).lower()
            
            for category, terms in keywords.items():
                for term in terms:
                    if term.lower() in text_to_search:
                        found[category].append(f"{code}: {name}")
                        break
        
        for cat, items in found.items():
            print(f"\n--- {cat} ---")
            for item in items[:5]: # Limit to 5 per category
                print(item)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_datasets()
