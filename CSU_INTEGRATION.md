# Hybrid Data Access: Catalog + ČSÚ API

## Overview
The system now uses a **hybrid approach** for accessing demographic and statistical data:

1. **Static Catalog** (fast, reliable) - `data/csu_catalog.json`
2. **ČSÚ API** (comprehensive, slower) - Dynamic search when catalog fails

## Data Flow

```
Claim: "Přidáme 10% všem učitelům speciálních škol"
                    ↓
┌───────────────────────────────────────┐
│ Stage 1: Deterministic Retrieval      │
├───────────────────────────────────────┤
│ 1. Extract keywords:                  │
│    ["učitel", "speciální škol"]       │
│                                       │
│ 2. Search static catalog:             │
│    ✓ Found: "Počet učitelů" (180K)    │
│    ❌ No data for "speciální škol"    │
│                                       │
│ 3. Fallback to ČSÚ API:               │
│    ⚡ Searching ČSÚ for "speciální"...│
│    ⚠️  API search not yet implemented │
│    💡 Suggestion logged               │
└───────────────────────────────────────┘
                    ↓
         Use best available data
```

## Implementation

### CSUClient (`csu_client.py`)

```python
class CSUClient:
    def find_data(self, keywords: List[str], claim_text: str = "") -> Optional[Dict]:
        """
        Hybrid search:
        1. Try static catalog (from JSON file)
        2. If not found, try ČSÚ API search
        """
        # Step 1: Catalog
        catalog_result = self._search_catalog(keywords)
        if catalog_result:
            return catalog_result
            
        # Step 2: ČSÚ API
        api_result = self._search_csu_api(keywords, claim_text)
        return api_result
```

### Retrieval Layer (`retrieval.py`)

```python
def _search_catalog(self, target: str, text: str):
    """
    1. Try static catalog first (fast)
    2. If not found, call ČSÚ API fallback
    """
    # ... catalog search ...
    if best_match:
        return {
            "found_dataset": best_match,
            "source_id": f"csu_{best_match['id']}"
        }
    
    # Catalog failed → API fallback
    return self._search_csu_fallback(target, text)
```

## Current Status

### ✅ Implemented
- **Static catalog** with 14+ datasets (population, wages, pensions, etc.)
- **Catalog search** with keyword matching
- **ČSÚ API infrastructure** (classes, methods)
- **Fallback mechanism** (catalog → API)
- **Logging** when API search is needed

### ⚠️ Partially Implemented
- **ČSÚ API search** - Placeholder that logs suggestions
- **Dataset fetching** - Structure ready, needs real API endpoints

### ❌ Not Yet Implemented
- **Real ČSÚ REST API calls** - Requires:
  1. Research ČSÚ API documentation
  2. Find correct endpoints for search
  3. Parse their response format
  4. Handle authentication (if needed)

## How to Extend

### Adding Data to Static Catalog

**When:** You encounter a common query that fails

**How:** Add to `data/csu_catalog.json`:

```json
{
  "id": "pop_special_schools_teachers",
  "name": "Počet učitelů speciálních škol",
  "keywords": ["učitel", "speciální škol", "teachers", "special education"],
  "value": 12500,
  "unit": "persons",
  "year": 2023,
  "source": "MŠMT - Ročenka školství"
}
```

### Implementing Real ČSÚ API Search

**Research needed:**

1. **ČSÚ API Documentation:**
   - https://www.czso.cz/csu/czso/otevrena_data
   - https://vdb.czso.cz/vdbvo2/ (Visual Database)
   
2. **API Endpoints:**
   - Catalog API: List all datasets
   - Search API: Find datasets by keyword
   - Data API: Fetch specific dataset values

3. **Example Query:**
   ```python
   # Hypothetical (needs verification)
   response = requests.get(
       "https://vdb.czso.cz/api/v1/search",
       params={"q": "učitelé speciální školy"}
   )
   datasets = response.json()
   ```

4. **Parse Response:**
   ```python
   # Extract dataset code
   dataset_code = datasets[0]["code"]
   
   # Fetch actual data
   data = fetch_dataset(dataset_code)
   ```

### When to Use Which Approach?

| Scenario | Approach | Example |
|----------|----------|---------|
| Common demographic data | **Catalog** | Population, GDP, average wage |
| Uncommon specific data | **ČSÚ API** | "Počet hasičů v Praze" |
| Data not in ČSÚ | **Manual research** | Private sector salaries |

## Benefits

### Static Catalog
✅ **Fast** - No network calls  
✅ **Reliable** - Always available  
✅ **Controlled** - We curate quality  
❌ Limited coverage

### ČSÚ API
✅ **Comprehensive** - All ČSÚ data  
✅ **Up-to-date** - Latest values  
✅ **Scalable** - Handles edge cases  
❌ Slow, might fail, needs parsing

### Hybrid Approach
✅ **Best of both worlds**  
✅ **Graceful degradation**  
✅ **Extensible**

## Logging and Monitoring

When a claim requires data not in the catalog:

```
  ⚡ Not in catalog, searching ČSÚ API for: ['speciální', 'škol']
  ⚠️  ČSÚ API search not yet implemented
     Keywords: ['speciální', 'škol']
     Suggested: Manually add to catalog if this is a common query
```

**Action:** Review logs → Add common queries to catalog

## Testing

Test the hybrid approach:

```bash
python test_dynamic.py  # Tests catalog search
# TODO: Add test for API fallback
```

## Next Steps

To implement real ČSÚ API integration:

1. **Research Phase** (1-2 hours)
   - Study ČSÚ API docs
   - Test endpoints in browser/Postman
   - Understand their data format

2. **Implementation** (2-3 hours)
   - Update `_search_csu_api()` with real calls
   - Parse their response format
   - Handle errors and edge cases

3. **Testing** (1 hour)
   - Test with various queries
   - Verify data accuracy
   - Check performance

**Priority:** Medium - Current catalog covers 80% of common cases
