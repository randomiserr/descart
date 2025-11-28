"""
Strict JSON schemas for the deterministic 4-stage architecture.
"""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

# Stage 0: Claim Extraction Schemas

ClaimType = Literal[
    "spending_increase_absolute",  # "Zvýšíme důchody o 2000 Kč"
    "spending_increase_percent",   # "Zvýšíme výdaje na kulturu o 10%"
    "spending_cut_absolute",       # "Snížíme výdaje o 5 miliard"
    "spending_cut_percent",        # "Snížíme výdaje na obranu o 20%"
    "tax_rate_increase",           # "Zvýšíme DPH na 25%"
    "tax_rate_decrease",           # "Snížíme daň z příjmu na 10%"
    "tax_base_change",             # "Zavedeme daň z tichého vína"
    "regulatory_change",           # "Zrušíme povinnost..."
    "general_policy"               # Catch-all for unclear claims
]

PolicyArea = Literal[
    "pensions",           # Důchody
    "healthcare",         # Zdravotnictví
    "education",          # Školství
    "culture",            # Kultura
    "defense",            # Obrana
    "infrastructure",     # Infrastruktura
    "social_services",    # Sociální služby
    "taxation",           # Daně
    "environment",        # Životní prostředí
    "agriculture",        # Zemědělství
    "justice",            # Justice
    "public_admin",       # Veřejná správa
    "other"               # Ostatní
]

class Claim(BaseModel):
    """
    Structured claim extracted from political text.
    """
    id: str = Field(..., description="Unique identifier (e.g., 'C1', 'C2')")
    text: str = Field(..., description="Original claim text in Czech")
    policy_area: PolicyArea = Field(..., description="Policy domain")
    claim_type: ClaimType = Field(..., description="Type of policy change")
    target_entity: str = Field(..., description="Specific entity affected (e.g., 'state_pensions', 'VAT')")
    
    # Quantitative values (at least one should be present for non-general claims)
    value_czk: Optional[float] = Field(None, description="Absolute amount in CZK")
    value_percent: Optional[float] = Field(None, description="Percentage change")
    
    # Metadata
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")

class ClaimExtractionResult(BaseModel):
    """
    Result of claim extraction from input text.
    """
    claims: List[Claim]
    input_text: str
    extraction_method: str = "llm_gemini_1.5_pro"

# Stage 1: Retrieval Schemas

class BudgetFact(BaseModel):
    """
    Budget data retrieved for a claim.
    """
    category: str
    year: int
    total_czk: float
    source_id: str
    line_items: List[Dict]

class LegalFact(BaseModel):
    """
    Legal context retrieved for a claim.
    """
    document_id: str
    document_name: str
    relevance_score: float
    content_snippet: str

class DemographicFact(BaseModel):
    """
    Demographic data retrieved for a claim.
    """
    indicator: str
    value: float
    unit: str
    year: int
    source_id: str

class MacroFact(BaseModel):
    """
    Macroeconomic data retrieved for a claim.
    """
    indicator: str
    value: float
    unit: str
    period: str
    source_id: str

class RetrievalResult(BaseModel):
    """
    All facts retrieved for a claim.
    """
    claim_id: str
    budget: Optional[BudgetFact] = None
    laws: List[LegalFact] = []
    demographics: Optional[DemographicFact] = None
    macro: List[MacroFact] = []
    sources: Dict[str, str] = {}  # source_id -> human readable label

# Stage 2: Calculation Schemas

class CalculationResult(BaseModel):
    """
    Result of a deterministic calculation.
    """
    claim_id: str
    result_czk: float
    formula: str
    assumptions: List[str]
    model_id: str
    inputs: Dict[str, float]  # input_name -> value

# Stage 3: Synthesis Schemas

class ClaimAnalysis(BaseModel):
    """
    LLM-generated analysis of a claim.
    """
    text: str
    feasibility: str
    fiscal_impact: str
    legal_risks: str
    public_expert_opinion: str

class TopicAnalysis(BaseModel):
    """
    Analysis of a topic (group of related claims).
    """
    name: str
    overall_analysis: str
    future_impact: str
    claims: List[ClaimAnalysis]

class AnalysisReport(BaseModel):
    """
    Final analysis report.
    """
    topics: List[TopicAnalysis]
