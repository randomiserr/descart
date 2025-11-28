import json
import os
from typing import List, Dict, Optional

# Constants for data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LAWS_PATH = os.path.join(DATA_DIR, 'laws.json')
BUDGET_PATH = os.path.join(DATA_DIR, 'budget.json')
MACRO_PATH = os.path.join(DATA_DIR, 'macro.json')

class DataLayer:
    def __init__(self):
        # Prefer extracted data if available
        if os.path.exists(os.path.join(DATA_DIR, 'laws_extracted.json')):
            self.laws = self._load_json(os.path.join(DATA_DIR, 'laws_extracted.json'))
            print("Loaded laws from laws_extracted.json")
        else:
            self.laws = self._load_json(LAWS_PATH)
            print("Loaded mock laws from laws.json")
            
        # Load Codelists
        self.codelists = {}
        items_path = os.path.join(DATA_DIR, 'codelists', 'items.json')
        if os.path.exists(items_path):
            self.codelists['items'] = self._load_json(items_path)
            print(f"Loaded {len(self.codelists['items'])} budget item names.")
            
        # Load Budget (CSV or Mock)
        self.budget = []
        if os.path.exists(os.path.join(DATA_DIR, 'budget_2025.csv')):
            print("Attempting to load real budget from budget_2025.csv...")
            self.budget = self._load_budget_csv(os.path.join(DATA_DIR, 'budget_2025.csv'))
        
        if not self.budget:
            print("Real budget empty or failed to parse. Falling back to mock budget.json")
            self.budget = self._load_json(BUDGET_PATH)
        else:
            print(f"Loaded {len(self.budget)} items from real budget.")

        self.macro = self._load_json(MACRO_PATH)

    def _load_json(self, path: str) -> List[Dict]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return []

    def _load_budget_csv(self, path: str) -> List[Dict]:
        """
        Parses the Monitor CSV (MIS-RIS) into a simplified list of dicts.
        """
        data = []
        try:
            import csv
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        code = row.get('ZCMMT_ITM', '0000')
                        chapter = row.get('0FM_AREA', '000')
                        amount = 0.0
                        
                        # Try to find amount in columns
                        for k, v in row.items():
                            if 'AMOUNT' in k or 'SUM' in k or 'HODNOTA' in k:
                                try:
                                    val = float(v.replace(',', '.').replace(' ', ''))
                                    amount = val
                                    break
                                except:
                                    pass
                        
                        # Fallback to last column
                        if amount == 0.0:
                            vals = list(row.values())
                            if vals:
                                try:
                                    amount = float(vals[-1].replace(',', '.').replace(' ', ''))
                                except:
                                    pass

                        if amount > 0:
                            # Resolve Name from Codelist
                            item_name = self.codelists.get('items', {}).get(code, f"Item {code}")
                            
                            data.append({
                                "category_code": code,
                                "category_name": f"{item_name} (Ch. {chapter})",
                                "amount_czk": amount,
                                "year": 2025,
                                "type": "Expenditure",
                                "source": "Monitor CSV"
                            })
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error parsing budget CSV: {e}")
        return data

    def get_budget(self, category_query: str, year: int = 2024) -> List[Dict]:
        """
        Retrieve budget items matching the query and year.
        """
        results = []
        query_lower = category_query.lower()
        for item in self.budget:
            # If year is 2025 (real data), ignore the requested year 2024 for now or map it
            item_year = item.get('year')
            if (item_year == year or item_year == 2025) and query_lower in item.get('category_name', '').lower():
                results.append(item)
        return results

    def get_macro_snapshot(self, indicators: List[str] = None) -> Dict[str, Dict]:
        """
        Get latest values for requested macro indicators.
        If indicators is None, return all.
        """
        # Check if we have real macro data
        real_macro_path = os.path.join(DATA_DIR, 'macro_real.json')
        if os.path.exists(real_macro_path):
            try:
                with open(real_macro_path, 'r') as f:
                    index = json.load(f)
                
                snapshot = {}
                for entry in index:
                    name = entry['indicator']
                    if indicators is None or name in indicators:
                        # Load the CSV and get the last value
                        csv_path = os.path.join(DATA_DIR, entry['source_file'])
                        if os.path.exists(csv_path):
                            with open(csv_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                if len(lines) > 1:
                                    # Very naive parsing of last line
                                    last_line = lines[-1].strip()
                                    # Assuming value is the last column? This is risky.
                                    # Let's just return the raw line for the LLM to parse if needed
                                    # Or try to find a number.
                                    import re
                                    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", last_line)
                                    val = float(numbers[-1]) if numbers else 0.0
                                    
                                    snapshot[name] = {
                                        "indicator": name,
                                        "value": val,
                                        "unit": "raw_csv_last_val",
                                        "period": "latest",
                                        "source": "CSU API"
                                    }
                if snapshot:
                    return snapshot
            except Exception as e:
                print(f"Error reading real macro data: {e}")

        # Fallback to mock
        snapshot = {}
        for item in self.macro:
            ind_name = item.get('indicator')
            if indicators is None or ind_name in indicators:
                snapshot[ind_name] = item
        return snapshot

    def get_law_context(self, query: str, domains: List[str] = None) -> List[Dict]:
        """
        Semantic search using Vector DB (Chroma).
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            db_path = os.path.join(DATA_DIR, 'vectordb')
            if not os.path.exists(db_path):
                print("Vector DB not found. Falling back to keyword search.")
                return self._keyword_search_laws(query, domains)

            # Initialize Client (Persistent)
            client = chromadb.PersistentClient(path=db_path)
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            
            try:
                collection = client.get_collection(name="laws_collection", embedding_function=ef)
            except Exception:
                print("Collection not found. Falling back.")
                return self._keyword_search_laws(query, domains)
            
            # Query
            print(f"Vector searching for: '{query}'...")
            search_res = collection.query(
                query_texts=[query],
                n_results=5
            )
            
            results = []
            if search_res['ids'] and search_res['ids'][0]:
                for i, doc_id in enumerate(search_res['ids'][0]):
                    doc_text = search_res['documents'][0][i]
                    meta = search_res['metadatas'][0][i]
                    dist = search_res['distances'][0][i]
                    
                    # Reconstruct a "law" object
                    law_obj = {
                        "id": doc_id,
                        "content_chunk": doc_text,
                        "source_document": meta.get('source_document'),
                        "domain_tags": meta.get('domain_tags', '').split(',')
                    }
                    
                    results.append({
                        "law": law_obj,
                        "relevance_score": 1.0 - dist # Rough approximation
                    })
            
            return [r['law'] for r in results]
            
        except Exception as e:
            print(f"Vector search error: {e}. Falling back to keyword search.")
            return self._keyword_search_laws(query, domains)

    def _keyword_search_laws(self, query: str, domains: List[str] = None) -> List[Dict]:
        """
        Fallback: Semantic search simulation (keyword matching) over laws.
        """
        results = []
        query_terms = query.lower().split()
        
        for law in self.laws:
            # Filter by domain if specified
            if domains:
                law_domains = law.get('domain_tags', [])
                if not any(d in law_domains for d in domains):
                    continue
            
            # Simple keyword match score
            content = law.get('content_chunk', '').lower()
            source = law.get('source_document', '').lower()
            
            score = 0
            for term in query_terms:
                if term in content:
                    score += 2
                if term in source:
                    score += 1
            
            if score > 0:
                results.append({
                    "law": law,
                    "relevance_score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return [r['law'] for r in results]

    def get_tax_revenue_estimate(self, tax_type: str) -> Optional[Dict]:
        """
        Get base revenue for a tax to estimate impact.
        """
        # Simple lookup in budget revenues
        for item in self.budget:
            if item.get('type') == 'Revenue' and tax_type.lower() in item.get('category_code', '').lower():
                return item
        return None

    def search_web(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the web for recent news/context using DuckDuckGo.
        """
        results = []
        try:
            from duckduckgo_search import DDGS
            
            print(f"Searching web for: '{query}'...")
            with DDGS() as ddgs:
                # Use 'news' backend for better relevance to current events
                # or 'text' for general search. Let's try general text first as it's broader.
                ddg_results = list(ddgs.text(query, max_results=max_results))
                
                for r in ddg_results:
                    results.append({
                        "title": r.get('title'),
                        "link": r.get('href'),
                        "snippet": r.get('body'),
                        "source": "DuckDuckGo"
                    })
        except Exception as e:
            print(f"Web search error: {e}")
            
        return results

# Global instance
data_layer = DataLayer()

# Tool functions exposed to the Orchestrator
def get_budget(category_query: str, year: int = 2024) -> List[Dict]:
    return data_layer.get_budget(category_query, year)

def get_macro_snapshot(indicators: List[str] = None) -> Dict[str, Dict]:
    return data_layer.get_macro_snapshot(indicators)

def get_law_context(query: str, domains: List[str] = None) -> List[Dict]:
    return data_layer.get_law_context(query, domains)

def get_tax_revenue_estimate(tax_type: str) -> Optional[Dict]:
    return data_layer.get_tax_revenue_estimate(tax_type)

def search_web(query: str, max_results: int = 5) -> List[Dict]:
    return data_layer.search_web(query, max_results)
