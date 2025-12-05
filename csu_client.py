"""
ČSÚ (Czech Statistical Office) API Client.
Fetches demographic and statistical data from DataStat API.
"""

import requests
from typing import Dict, List, Optional, Any
import json
import os

class CSUClient:
    """
    Client for Czech Statistical Office (ČSÚ) DataStat API.
    Documentation: https://csu.gov.cz/zakladni-informace-pro-pouziti-api-datastatu
    
    Hybrid approach:
    1. Try to fetch from static catalog (fast, reliable)
    2. If not found, search ČSÚ API (slow, but comprehensive)
    """
    
    BASE_URL = "https://vdb.czso.cz/vdbvo2"
    CATALOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'csu_catalog.json')
    
    def __init__(self):
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> List[Dict]:
        """Load static catalog."""
        if os.path.exists(self.CATALOG_PATH):
            try:
                with open(self.CATALOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading catalog: {e}")
        return []
    
    def find_data(self, keywords: List[str], claim_text: str = "") -> Optional[Dict]:
        """
        Find data by keywords. Uses hybrid approach:
        1. Search static catalog first (fast)
        2. If not found, search ČSÚ API (slow but comprehensive)
        
        Args:
            keywords: List of search terms (e.g., ["hasiči", "firefighters"])
            claim_text: Original claim text for context
            
        Returns:
            Dataset with 'value', 'unit', 'source', etc.
        """
        # Step 1: Try catalog first
        catalog_result = self._search_catalog(keywords)
        if catalog_result:
            print(f"  ✓ Found in catalog: {catalog_result['name']}")
            return catalog_result
        
        # Step 2: Try ČSÚ API search
        print(f"  ⚡ Not in catalog, searching ČSÚ API for: {keywords}")
        api_result = self._search_csu_api(keywords, claim_text)
        if api_result:
            print(f"  ✓ Found via ČSÚ API: {api_result.get('name', 'Unknown')}")
            return api_result
        
        print(f"  ❌ No data found for: {keywords}")
        return None
    
    def _search_catalog(self, keywords: List[str]) -> Optional[Dict]:
        """Search the static catalog."""
        best_match = None
        max_score = 0
        
        for dataset in self.catalog:
            score = 0
            for keyword in keywords:
                # Check in keywords field
                for cat_keyword in dataset.get("keywords", []):
                    if keyword.lower() in cat_keyword.lower():
                        score += 2
                # Check in name
                if keyword.lower() in dataset.get("name", "").lower():
                    score += 1
            
            if score > max_score:
                max_score = score
                best_match = dataset
        
        return best_match if max_score > 0 else None
    
    def _search_csu_api(self, keywords: List[str], context: str = "") -> Optional[Dict]:
        """
        Search ČSÚ API for datasets matching keywords.
        
        Note: This is a placeholder implementation. Real ČSÚ API search
        would require understanding their catalog structure.
        """
        try:
            # ČSÚ has multiple APIs:
            # 1. Data API (vdb.czso.cz) - for actual data
            # 2. Catalog API - for dataset metadata
            # 3. REST API - for queries
            
            # For now, we'll try a simple approach:
            # Search their public data catalog
            search_url = "https://vdb.czso.cz/vdbvo2/faces/cs/index.jsf"
            
            # TODO: Implement actual API search
            # This requires:
            # 1. Finding the right API endpoint
            # 2. Understanding their search parameters
            # 3. Parsing their response format
            
            # Placeholder: Log that we attempted search
            print(f"  ⚠️  ČSÚ API search not yet implemented")
            print(f"     Keywords: {keywords}")
            print(f"     Suggested: Manually add to catalog if this is a common query")
            
            return None
            
        except Exception as e:
            print(f"  ❌ ČSÚ API error: {e}")
            return None
    
    def fetch_dataset(self, dataset_code: str) -> Optional[Dict]:
        """
        Fetch a specific dataset by code.
        
        Args:
            dataset_code: ČSÚ dataset code (e.g., "25-3011r0")
            
        Returns:
            Dataset with latest values
        """
        try:
            # ČSÚ REST API endpoint (example)
            url = f"{self.BASE_URL}/rest/dataset/{dataset_code}/metadata"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_dataset(data)
        except Exception as e:
            print(f"Error fetching dataset {dataset_code}: {e}")
        
        return None
    
    def _parse_dataset(self, data: Dict) -> Dict:
        """Parse ČSÚ dataset format."""
        # ČSÚ uses various formats (JSON-STAT, CSV, XML)
        # This is a simplified parser
        try:
            if "value" in data:
                return {
                    "name": data.get("label", "Unknown"),
                    "value": data["value"][0] if isinstance(data["value"], list) else data["value"],
                    "unit": data.get("unit", "unknown"),
                    "year": data.get("updated", "unknown"),
                    "source": "ČSÚ API"
                }
        except:
            pass
        
        return None
    
    # Legacy methods (for backward compatibility)
    def get_population_pensioners(self, year: int = 2024) -> int:
        """Get total number of pension recipients."""
        result = self.find_data(["důchodci", "pensioners"])
        return int(result["value"]) if result else 2_367_000
    
    def get_population_total(self, year: int = 2024) -> int:
        """Get total population."""
        result = self.find_data(["populace", "obyvatel", "population"])
        return int(result["value"]) if result else 10_827_529
    
    def get_avg_pension(self, year: int = 2024) -> float:
        """Get average pension amount."""
        result = self.find_data(["důchod", "pension", "průměrný"])
        return float(result["value"]) if result else 20_216.0
    
    def get_gdp(self, year: int = 2024) -> float:
        """Get nominal GDP."""
        result = self.find_data(["GDP", "HDP", "produkt"])
        return float(result["value"]) if result else 7.3e12

