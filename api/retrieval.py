"""
Deterministic retrieval layer for Stage 1.
Uses dynamic catalog search to find relevant data for claims.
"""

from typing import Dict, List, Optional, Any
import json
import os
import tools

# Path to the data catalog
CATALOG_PATH = os.path.join(os.path.dirname(__file__), 'data', 'csu_catalog.json')

class DeterministicRetrieval:
    """
    Retrieves data by searching a catalog of available datasets.
    """
    
    def __init__(self):
        self.catalog = self._load_catalog()
        
        # Keep budget map for now as it's specific to state budget structure
        self.policy_budget_map = {
            "pensions": ["411"],
            "healthcare": ["313"],
            "education": ["333"],
            "culture": ["334"],
            "defense": ["307"],
            "infrastructure": ["327", "328"],
            "social_services": ["412", "413"],
            "environment": ["315"],
            "agriculture": ["322"],
            "justice": ["330"],
            "public_admin": ["301", "302"]
        }

    def _load_catalog(self) -> List[Dict]:
        """Load the dataset catalog."""
        if os.path.exists(CATALOG_PATH):
            try:
                with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading catalog: {e}")
        return []

    def retrieve_facts(self, claim: Dict) -> Dict:
        """
        Retrieve facts by dynamically searching for relevant data.
        """
        claim_id = claim.get("id", "unknown")
        policy_area = claim.get("policy_area", "other")
        target_entity = claim.get("target_entity", "")
        text = claim.get("text", "")
        
        # 1. Dynamic Data Search
        # Search for any data in our catalog that matches the target entity
        relevant_data = self._search_catalog(target_entity, text)
        
        # 2. Budget Data (Fixed mapping still useful for broad context)
        budget_data = self._get_budget_facts(policy_area)
        
        # 3. Macro Data (Always useful context)
        macro_data = tools.get_macro_snapshot(["GDP", "Inflation", "RealWageGrowth"])
        
        # 4. Web Search (Latest context)
        web_search = self._get_web_search(claim)
        
        facts = {
            "claim_id": claim_id,
            "relevant_data": relevant_data,  # The dynamically found data
            "budget": budget_data,
            "macro": macro_data,
            "web_search": web_search,
            "sources": {}
        }
        
        self._build_source_registry(facts)
        return facts

    def _search_catalog(self, target: str, text: str) -> Dict[str, Any]:
        """
        Find the most relevant dataset using hybrid approach:
        1. Static catalog (fast)
        2. ČSÚ API (comprehensive, but slower)
        """
        if not self.catalog:
            return self._search_csu_fallback(target, text)
            
        query_terms = (target + " " + text).lower().split()
        best_match = None
        max_score = 0
        
        # Try static catalog first
        for dataset in self.catalog:
            score = 0
            # Check keywords
            for keyword in dataset.get("keywords", []):
                if keyword in target.lower():
                    score += 3  # High match if in target entity
                if keyword in text.lower():
                    score += 1  # Low match if just in text
            
            if score > max_score:
                max_score = score
                best_match = dataset
        
        if best_match and max_score > 0:
            return {
                "found_dataset": best_match,
                "match_score": max_score,
                "source_id": f"csu_{best_match['id']}"
            }
        
        # Catalog failed, try ČSÚ API
        return self._search_csu_fallback(target, text)
    
    def _search_csu_fallback(self, target: str, text: str) -> Dict[str, Any]:
        """
        Fallback to ČSÚ API search when catalog doesn't have the data.
        """
        try:
            from csu_client import CSUClient
            csu = CSUClient()
            
            # Extract keywords from target and text
            keywords = target.split() + text.split()
            keywords = [k.strip() for k in keywords if len(k) > 3][:5]  # Limit to 5 most relevant
            
            # Try to find data dynamically
            result = csu.find_data(keywords, claim_text=text)
            
            if result:
                return {
                    "found_dataset": result,
                    "match_score": 1,  # Lower score than catalog
                    "source_id": f"csu_api_{result.get('name', 'unknown').replace(' ', '_')[:30]}"
                }
        except Exception as e:
            print(f"ČSÚ API fallback error: {e}")
        
        return {}

    def _get_budget_facts(self, policy_area: str) -> Dict:
        """Get budget data using fixed code mapping."""
        codes = self.policy_budget_map.get(policy_area, [])
        if not codes:
            return {"total_czk": 0, "line_items": []}
            
        items = []
        for code in codes:
            items.extend(tools.get_budget_by_code(code))
            
        total = sum(item.get("amount_czk", 0) for item in items)
        return {
            "category": policy_area,
            "total_czk": total,
            "source_id": f"budget_2025_chapter_{codes[0] if codes else 'unknown'}",
            "line_items": items[:5]
        }

    def _get_web_search(self, claim: Dict) -> List[Dict]:
        text = claim.get("text", "")
        search_query = f"{text} diskuze názory experti"
        results = tools.search_web(search_query, max_results=3)
        for i, result in enumerate(results):
            result["source_id"] = f"web_search_{i+1}"
        return results

    def _build_source_registry(self, facts: Dict):
        sources = {}
        
        # Dynamic Data Source
        data = facts.get("relevant_data", {})
        if data and "found_dataset" in data:
            ds = data["found_dataset"]
            sources[data["source_id"]] = f"{ds['source']}: {ds['name']} ({ds['year']})"
            
        # Budget Source
        if facts["budget"].get("source_id"):
             sources[facts["budget"]["source_id"]] = "Státní rozpočet 2025"
             
        # Web Sources
        for result in facts["web_search"]:
            if result.get("source_id"):
                sources[result["source_id"]] = f"{result.get('title', 'Web')}"
                
        facts["sources"] = sources
