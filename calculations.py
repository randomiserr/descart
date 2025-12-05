"""
Stage 2: Calculation Engine.
Generic formulas that adapt to dynamically retrieved data.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class CalculationResult(BaseModel):
    cost_czk: Optional[float] = None
    revenue_czk: Optional[float] = None
    formula_used: str
    assumptions: List[str]
    inputs_used: Dict[str, Any]
    confidence: float = 1.0

class Formula(ABC):
    @abstractmethod
    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

# ==============================================================================
# GENERIC FORMULAS
# ==============================================================================

class PerCapitaMultiplication(Formula):
    """
    Generic: Amount * Population Count
    Adapts to whatever population data was found in retrieval.
    """
    @property
    def name(self) -> str:
        return "per_capita_multiplication"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        amount = claim.get("value_czk")
        
        # Look for ANY relevant dataset found in retrieval
        relevant_data = facts.get("relevant_data", {})
        dataset = relevant_data.get("found_dataset")
        
        if not amount or not dataset or dataset.get("unit") != "persons":
            return CalculationResult(
                formula_used=self.name,
                assumptions=["Missing amount or relevant population data"],
                inputs_used={},
                confidence=0.0
            )
            
        population_count = dataset.get("value", 0)
        cost = amount * population_count
        
        return CalculationResult(
            cost_czk=cost,
            formula_used=f"{population_count:,.0f} ({dataset['name']}) * {amount:,.0f} CZK",
            assumptions=[f"Applied to all: {dataset['name']}"],
            inputs_used={
                "population": population_count,
                "amount": amount,
                "source_id": relevant_data.get("source_id")
            }
        )

class RateApplication(Formula):
    """
    Generic: Base Amount * Rate
    Used for percentage increases/decreases.
    """
    @property
    def name(self) -> str:
        return "rate_application"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        percent = claim.get("value_percent")
        
        # Try to find a base amount (Budget or Macro or Catalog)
        base_amount = 0
        base_name = "Unknown Base"
        
        # 1. Try Budget
        if facts.get("budget", {}).get("total_czk", 0) > 0:
            base_amount = facts["budget"]["total_czk"]
            base_name = f"Budget: {facts['budget']['category']}"
            
        # 2. Try Catalog Data (e.g. GDP)
        elif facts.get("relevant_data", {}).get("found_dataset", {}).get("unit") == "CZK":
             ds = facts["relevant_data"]["found_dataset"]
             base_amount = ds["value"]
             base_name = ds["name"]
             
        if not percent or base_amount == 0:
             return CalculationResult(
                formula_used=self.name,
                assumptions=["Missing percentage or base amount"],
                inputs_used={},
                confidence=0.0
            )
            
        cost = base_amount * (percent / 100.0)
        
        return CalculationResult(
            cost_czk=cost,
            formula_used=f"{base_amount:,.0f} ({base_name}) * {percent}%",
            assumptions=[f"Applied rate to {base_name}"],
            inputs_used={"base": base_amount, "rate": percent}
        )

class SimpleAddition(Formula):
    """
    Direct cost (e.g. "We will spend 1 billion")
    """
    @property
    def name(self) -> str:
        return "simple_addition"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        amount = claim.get("value_czk")
        if not amount:
             return CalculationResult(formula_used=self.name, assumptions=[], inputs_used={}, confidence=0.0)
             
        return CalculationResult(
            cost_czk=amount,
            formula_used=f"Direct Cost: {amount:,.0f} CZK",
            assumptions=[],
            inputs_used={"amount": amount}
        )

# ==============================================================================
# SPECIFIC FORMULAS
# ==============================================================================

class PensionValorization(Formula):
    """
    Standard pension valorization formula.
    Cost = (Inflation + 1/3 Real Wage Growth) * Avg Pension * Num Pensioners * 12
    """
    @property
    def name(self) -> str:
        return "pension_valorization"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        macro = facts.get("macro", {})
        inflation = macro.get("Inflation", {}).get("value", 2.5)
        wage_growth = macro.get("RealWageGrowth", {}).get("value", 1.5)
        
        # Try to find pension data in catalog or fallback
        relevant_data = facts.get("relevant_data", {})
        dataset = relevant_data.get("found_dataset")
        
        num_pensioners = 0
        avg_pension = 20000 # Fallback
        
        if dataset and "důchod" in dataset.get("name", "").lower():
            num_pensioners = dataset.get("value", 0)
        else:
            # Fallback to hardcoded if catalog search failed for this specific complex formula
            num_pensioners = 2367000 
            
        increase_percent = inflation + (1/3 * wage_growth)
        monthly_increase = avg_pension * (increase_percent / 100.0)
        total_annual_cost = monthly_increase * num_pensioners * 12
        
        return CalculationResult(
            cost_czk=total_annual_cost,
            formula_used=f"({inflation}% Infl + 1/3*{wage_growth}% Wage) * {avg_pension} * {num_pensioners} * 12",
            assumptions=["Statutory valorization formula"],
            inputs_used={"inflation": inflation, "wage_growth": wage_growth, "pensioners": num_pensioners}
        )

class TaxRateChange(Formula):
    """
    Change in tax rate (VAT, Income Tax).
    Revenue Delta = Tax Base * (New Rate - Old Rate)
    """
    @property
    def name(self) -> str:
        return "tax_rate_change"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        new_rate = claim.get("value_percent")
        target = claim.get("target_entity", "").lower()
        
        # Get GDP - try catalog first, then use fallback
        gdp = 7.3e12 # Fallback
        relevant_data = facts.get("relevant_data", {})
        dataset = relevant_data.get("found_dataset")
        if dataset and dataset.get("id") == "gdp_nominal":
            gdp = dataset.get("value", gdp)
        
        # Estimate Tax Base (very rough approximation)
        # VAT Base ~ Consumption ~ 50% of GDP
        # Income Tax Base ~ Wages ~ 40% of GDP
        tax_base = 0
        base_name = "Unknown"
        current_rate = 0
        
        if "dph" in target or "vat" in target:
            tax_base = gdp * 0.5
            base_name = "Est. VAT Base (50% GDP)"
            current_rate = 21.0 # Standard rate
        elif "daň" in target and ("příjm" in target or "income" in target):
            tax_base = gdp * 0.4
            base_name = "Est. Income Base (40% GDP)"
            current_rate = 15.0 # Base rate
            
        if not new_rate or tax_base == 0:
             return CalculationResult(
                formula_used=self.name,
                assumptions=["Missing tax base or rate data"],
                inputs_used={},
                confidence=0.0
            )
            
        revenue_delta = tax_base * ((new_rate - current_rate) / 100.0)
        
        return CalculationResult(
            revenue_czk=revenue_delta,
            formula_used=f"{base_name} * ({new_rate}% - {current_rate}%)",
            assumptions=[f"Base estimated from GDP: {gdp:,.0f}", f"Current rate: {current_rate}%"],
            inputs_used={"tax_base": tax_base, "new_rate": new_rate, "old_rate": current_rate, "gdp": gdp}
        )

class DebtToGDP(Formula):
    """
    Calculates impact on Debt-to-GDP ratio.
    """
    @property
    def name(self) -> str:
        return "debt_to_gdp"

    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        # This is usually a target, not a cost calculation
        target_ratio = claim.get("value_percent")
        
        # Get GDP - try catalog first, then use fallback
        gdp = 7.3e12 # Fallback
        relevant_data = facts.get("relevant_data", {})
        dataset = relevant_data.get("found_dataset")
        if dataset and dataset.get("id") == "gdp_nominal":
            gdp = dataset.get("value", gdp)
        
        if not target_ratio:
             return CalculationResult(formula_used=self.name, assumptions=[], inputs_used={}, confidence=0.0)
             
        implied_debt = gdp * (target_ratio / 100.0)
        
        return CalculationResult(
            cost_czk=0, # It's a target, not a cost
            formula_used=f"Target Debt: {target_ratio}% of GDP",
            assumptions=[f"Implied Total Debt: {implied_debt:,.0f} CZK", f"GDP: {gdp:,.0f} CZK"],
            inputs_used={"gdp": gdp, "target_ratio": target_ratio}
        )

# ==============================================================================
# ENGINE
# ==============================================================================

class CalculationEngine:
    def __init__(self):
        self.formulas = {
            "per_capita": PerCapitaMultiplication(),
            "rate": RateApplication(),
            "direct": SimpleAddition(),
            "pension_valorization": PensionValorization(),
            "tax_rate": TaxRateChange(),
            "debt_gdp": DebtToGDP()
        }
        self.unsupported_log = []
    
    def calculate(self, claim: Dict, facts: Dict) -> CalculationResult:
        """
        Dynamically selects formula based on data availability.
        """
        claim_type = claim.get("claim_type")
        text = claim.get("text", "").lower()
        target = claim.get("target_entity", "").lower()
        
        # 1. Specific Complex Formulas
        if "valoriz" in text and ("důchod" in target or "pension" in target):
            return self.formulas["pension_valorization"].calculate(claim, facts)
            
        # Tax rate changes - check for DPH/VAT or income tax
        if ("dph" in target or "vat" in target) and claim.get("value_percent"):
            return self.formulas["tax_rate"].calculate(claim, facts)
        if ("daň" in target and ("příjm" in target or "income" in target)) and claim.get("value_percent"):
            return self.formulas["tax_rate"].calculate(claim, facts)

        if "dluh" in target and "hdp" in target:
             return self.formulas["debt_gdp"].calculate(claim, facts)

        # 2. Generic Formulas (The "Dynamic" Layer)
        # Per Capita
        if claim.get("value_czk") and facts.get("relevant_data", {}).get("found_dataset", {}).get("unit") == "persons":
            if "každ" in text or "per capita" in text or "pro" in text:
                return self.formulas["per_capita"].calculate(claim, facts)
        
        # Rate Application
        if claim.get("value_percent"):
            return self.formulas["rate"].calculate(claim, facts)
            
        # Direct Amount
        if claim.get("value_czk"):
            return self.formulas["direct"].calculate(claim, facts)
            
        # 3. Logging Unsupported
        self.unsupported_log.append({
            "claim_id": claim.get("id"),
            "text": claim.get("text"),
            "reason": "No matching formula or data found"
        })
        
        return CalculationResult(
            formula_used="none",
            assumptions=["No suitable formula or data found"],
            inputs_used={},
            confidence=0.0
        )
