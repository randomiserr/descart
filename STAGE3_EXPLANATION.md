# Stage 3: LLM Explanation - Implementation Summary

## Overview
Stage 3 ensures the LLM **never invents numbers**. All calculations come from Stage 2 (Python), and the LLM's job is **purely synthesis and explanation**.

## Key Changes

### 1. **Strict No-Calculation Policy**
The system prompt now includes:
```
🔴 KRITICKÁ PRAVIDLA:
1. NIKDY nevymýšlejte čísla ani výpočty
2. Používejte POUZE výsledky z sekce "MODELOVÉ VÝPOČTY"
3. Pokud výpočet chybí, napište: "Přesný fiskální dopad nebylo možné vypočítat."
```

### 2. **Temperature Lowered to 0.2**
```python
response = self.llm.generate_response(prompt, system_prompt, temperature=0.2)
```

This significantly reduces randomness and hallucinations.

### 3. **Calculation Results Prominently Displayed**
The prompt now includes:

```
MODELOVÉ VÝPOČTY (POUŽIJTE TYTO HODNOTY):

[Claim 1] "Přidáme 5000 Kč každému hasiči..."
  → NÁKLAD: 57,500,000 CZK
  → Formule: 11,500 (Počet hasičů) * 5,000 CZK
  → Předpoklady: Applied to all: Počet hasičů (HZS)
```

### 4. **Source Registry**
Instead of dumping raw data, the LLM receives:
- A **source registry** (mapping source_id → human-readable name)
- A **concise context summary** (not full JSON dumps)

Example:
```
DOSTUPNÉ ZDROJE:
- csu_pop_firefighters: HZS ČR: Počet hasičů (2023)
- budget_2025_chapter_307: Státní rozpočet 2025
- web_search_1: Diskuze o valorizaci důchodů
```

### 5. **Minimal Context Injection**
The LLM no longer receives:
- ❌ Full budget JSON dumps
- ❌ Full legal documents
- ❌ Raw macro data

Instead, it gets:
- ✅ Summary counts ("202007 budget items, total 1.9T CZK")
- ✅ Source titles ("Zákon o DPH, Zákon o daních z příjmů")
- ✅ Calculation results with exact formulas

## Data Flow (Stage 0 → 3)

```
┌──────────────┐
│  Stage 0     │  LLM (temp=0.2) extracts structured claims
│  Extraction  │  → {"text": "...", "value_czk": 5000, "target": "hasiči"}
└──────┬───────┘
       │
┌──────▼───────┐
│  Stage 1     │  Python searches catalog for "hasiči"
│  Retrieval   │  → Finds: {id: "pop_firefighters", value: 11500}
└──────┬───────┘
       │
┌──────▼───────┐
│  Stage 2     │  Python calculates: 5000 * 11500 = 57.5M CZK
│  Calculation │  → CalculationResult(cost_czk=57500000, formula="...")
└──────┬───────┘
       │
┌──────▼───────┐
│  Stage 3     │  LLM (temp=0.2) writes:
│  Explanation │  "Navýšení platů hasičů o 5000 Kč měsíčně bude
│              │   <cite source='Modelový výpočet'>stát 57,5 mil. CZK
│              │   ročně</cite> (11 500 hasičů × 5000 Kč)."
└──────────────┘
```

## Testing

Run `test_stage3.py` to verify:
- ✅ Full pipeline (Stages 0-3) executes
- ✅ Calculation results are included in the prompt
- ✅ LLM uses `<cite>` tags
- ✅ LLM references 'Modelový výpočet'

## Benefits

1. **Determinism**: Same claim → same calculation → same number
2. **Transparency**: Formula is shown ("X * Y")
3. **Auditability**: Sources are tracked (source_id)
4. **Accuracy**: LLM can't make arithmetic errors
5. **Factuality**: Temperature 0.2 reduces hallucinations

## Comparison: Before vs After

### Before (Old System)
```
Prompt: "Spočítejte dopad zvýšení platů hasičů o 5000 Kč"
LLM: "Odhaduji, že to bude stát asi 60-80 miliard Kč ročně..."
```
❌ Wrong by 1000x! (hallucinates "miliard" instead of "milion")

### After (Stage 3)
```
Prompt: "NÁKLAD: 57,500,000 CZK (Počet hasičů: 11,500 × 5,000 CZK)"
LLM: "Náklady jsou <cite source='Modelový výpočet'>57,5 mil. CZK</cite>"
```
✅ Correct! LLM just reformats the pre-calculated number.

## Future Enhancements

1. **Strict Schema Validation**: Validate that the LLM didn't add any extra numbers
2. **Number Extraction Test**: Parse the report and verify all numbers came from Stage 2
3. **Citation Coverage**: Track which sources were actually cited vs. available
4. **A/B Testing**: Compare temperature 0.2 vs 0.0 vs 0.5 for quality

## Files Modified

- `orchestrator.py`:
  - `_synthesize_report()` - Refactored for Stage 3
  - `_format_calculations_for_prompt()` - New method
  - `_build_source_registry()` - New method
  - `_format_source_list()` - New method
  - `_format_context_for_prompt()` - New method

## Next Steps

You can now:
1. Test the full pipeline with `test_stage3.py`
2. Inspect the generated reports for citation quality
3. Add more formulas (Stage 2) to improve coverage
4. Review unsupported claims log to prioritize new formulas
