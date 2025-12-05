# Formula Library Documentation

## Overview
The Calculation Engine now supports a comprehensive library of formulas for Czech political claims analysis. The system combines **dynamic data discovery** (catalog-based) with **specific domain formulas** for accurate calculations.

## Formula Categories

### 1. Generic Formulas (Dynamic)
These formulas adapt to whatever data is found in the catalog:

#### `PerCapitaMultiplication`
- **Usage**: Cost per person/entity
- **Formula**: `Amount × Population Count`
- **Example**: "5000 Kč pro každého hasiče" → 5000 × 11,500 firefighters
- **Data Required**: Population dataset from catalog

#### `RateApplication`
- **Usage**: Percentage-based changes
- **Formula**: `Base Amount × Rate`
- **Example**: "Zvýšíme rozpočet o 10%" → Budget × 10%
- **Data Required**: Budget or monetary base

#### `SimpleAddition`
- **Usage**: Direct spending statements
- **Formula**: Direct cost
- **Example**: "1 miliarda na sport" → 1,000,000,000 CZK
- **Data Required**: None (claim value only)

### 2. Specific Formulas (Domain Knowledge)

#### `PensionValorization`
- **Usage**: Legal pension indexation
- **Formula**: `(Inflation + 1/3 × Real Wage Growth) × Avg Pension × Num Pensioners × 12`
- **Example**: "Provedeme zákonnou valorizaci důchodů"
- **Data Required**: Inflation, wage growth, pensioner count, avg pension
- **Confidence**: High (statutory formula)

#### `TaxRateChange`
- **Usage**: VAT or Income Tax rate changes
- **Formula**: `Tax Base × (New Rate - Old Rate)`
- **Tax Bases**:
  - VAT: ~50% of GDP
  - Income Tax: ~40% of GDP
- **Example**: "Zvýšíme DPH na 25%" → (50% GDP) × (25% - 21%)
- **Data Required**: GDP (from catalog or fallback)
- **Confidence**: Medium (estimated tax base)

#### `DebtToGDP`
- **Usage**: Debt-to-GDP ratio targets
- **Formula**: `Target Ratio × GDP`
- **Example**: "Snížíme dluh na 30% HDP"
- **Data Required**: GDP
- **Confidence**: High (simple ratio)

## Routing Logic

The `CalculationEngine` selects formulas using this hierarchy:

1. **Keyword-based Specific Formulas** (highest priority)
   - "valoriz" + "důchod" → `PensionValorization`
   - "DPH" / "daň z příjmů" → `TaxRateChange`
   - "dluh" + "HDP" → `DebtToGDP`

2. **Dynamic Generic Formulas** (data-driven)
   - Found population data + "každ" → `PerCapitaMultiplication`
   - Has percentage value → `RateApplication`
   - Has CZK value → `SimpleAddition`

3. **Unsupported** (log for future review)
   - Claim logged to `logs/unsupported_claims_YYYYMMDD_HHMMSS.json`

## Data Catalog Integration

All formulas can access data from `data/csu_catalog.json`:

```json
{
  "id": "pop_firefighters",
  "name": "Počet hasičů (HZS)",
  "keywords": ["hasiči", "požárníci", "firefighters"],
  "value": 11500,
  "unit": "persons",
  "year": 2023,
  "source": "HZS ČR"
}
```

### Available Datasets:
- **Population**: Total, pensioners, students, employees, teachers, doctors, nurses, firefighters, police
- **Economic**: Average wage, average pension, minimum wage, GDP
- **Macro**: Inflation, wage growth, unemployment (via macro API)

## Extensibility

### Adding a New Formula:
1. Create a class inheriting from `Formula`
2. Implement `calculate()` and `name` property
3. Add to `CalculationEngine.formulas` dictionary
4. Add routing logic in `CalculationEngine.calculate()`

### Adding New Data:
1. Add entry to `data/csu_catalog.json`
2. No code changes needed - dynamic retrieval will find it

## Testing

Run `test_formulas.py` to verify:
- Pension valorization
- VAT rate change
- Income tax rate change
- Debt-to-GDP target
- Unsupported claim logging

## Future Enhancements

Potential formulas to add:
- `ChangeRetirementAge`: Actuarial calculation of pension savings
- `ChangeBenefitAmount`: Social benefit impact
- `DeficitToGDP`: Budget deficit targets
- `InfrastructureInvestment`: ROI and maintenance costs
- `HealthcareCapacity`: Per-capita healthcare spending

## Logging

Unsupported claims are automatically logged to:
```
logs/unsupported_claims_20250128_192000.json
```

Structure:
```json
[
  {
    "claim_id": "C5",
    "text": "Změníme strukturu rozpočtu kompletně",
    "reason": "No matching formula or data found"
  }
]
```

Use these logs to identify gaps in coverage and prioritize new formulas.
