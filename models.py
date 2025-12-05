from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any

# --- Stage 1: Extraction ---
class Claim(BaseModel):
    id: str
    text: str
    domain: str          # "transport" | "tax" | ...
    policy_type: str     # "reject_eu_ice_ban" | ...
    notes: str = ""

class ExtractionResult(BaseModel):
    claims: List[Claim]
    research_queries: List[Dict[str, Any]] # claim_id -> queries list

# --- Stage 2: Planning ---
class ClaimQueries(BaseModel):
    claim_id: str
    queries: List[str]

class PlanningResult(BaseModel):
    mode: Literal["planning", "needs_additional_research"]
    additional_queries: Optional[List[ClaimQueries]] = None
    missing_information: Optional[List[str]] = None

# --- Stage 3: Research ---
class TavilyResult(BaseModel):
    query: str
    results: List[Dict[str, Any]]   # { "url": ..., "title": ..., "content": ... }

class ResearchResults(BaseModel):
    by_claim: Dict[str, List[TavilyResult]]  # claim_id -> results

# --- Stage 4: Hard Data ---
class HardData(BaseModel):
    laws: Dict[str, Any] = {}
    budget: Dict[str, Any] = {}
    macro: Dict[str, Any] = {}
    calc_results: Dict[str, Any] = {}

# --- Stage 5: Analysis ---
class DimensionQuantitative(BaseModel):
    status: Literal["modelled", "not_modelled", "insufficient_data"]
    value: Optional[float] = None
    method: str
    notes: str

class DimensionQualitative(BaseModel):
    status: Literal["supported", "partial", "speculative"]
    summary_cs: str
    channels: List[str]
    evidence_used: List[str]
    uncertainties: List[str]

class Dimension(BaseModel):
    name: str
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any

# --- Stage 1: Extraction (Topics) ---
class Topic(BaseModel):
    id: str
    name: str            # e.g., "Důchodová reforma", "Změna DPH"
    description: str     # Short summary of what this topic covers in the plan
    category: str        # "economy" | "social" | "transport" | "health" | "education" | "defense" | "other"

class ExtractionResult(BaseModel):
    topics: List[Topic]
    research_queries: List[Dict[str, Any]] # topic_id -> queries list

# --- Stage 2: Planning ---
class TopicQueries(BaseModel):
    topic_id: str
    queries: List[str]

class PlanningResult(BaseModel):
    mode: Literal["planning", "needs_additional_research", "analysis"]
    additional_queries: Optional[List[TopicQueries]] = None
    missing_information: Optional[List[str]] = None

# --- Stage 3: Research ---
class TavilyResult(BaseModel):
    query: str
    results: List[Dict[str, Any]]

class ResearchResults(BaseModel):
    by_topic: Dict[str, List[TavilyResult]]  # topic_id -> results

# --- Stage 4: Hard Data ---
class HardData(BaseModel):
    laws: Dict[str, Any] = {}
    budget: Dict[str, Any] = {}
    macro: Dict[str, Any] = {}
    calc_results: Dict[str, Any] = {}

# --- Stage 5: Analysis (Plan Level) ---
class Source(BaseModel):
    id: str
    name: str
    url: Optional[str] = None

class DimensionAssessment(BaseModel):
    dimension: str # "proveditelnost" | "ekonomicky_dopad" | "fiskalni_dopad" | "socialni_dopad" | "transnacionalni_vyznam" | "strategie_2035"
    score: int # 1-10 (where applicable, or 0 if neutral)
    verdict_cs: str # Short assessment
    explanation_cs: str # Detailed explanation
    key_risks: List[str]
    key_benefits: List[str]

class TopicAnalysis(BaseModel):
    topic_id: str
    topic_name: str
    current_state_cs: str = "" # Description of current problem/state with numbers
    summary_cs: str
    dimensions: List[DimensionAssessment]

class ExecutiveSummary(BaseModel):
    plan_name: str
    overview_cs: str
    main_benefits: List[str]
    main_risks: List[str]
    strategic_verdict_2035: str # The "Czechia 2035" lens
    recommendations: List[str] # Separated action items

class PlanAnalysis(BaseModel):
    mode: Literal["analysis"]
    executive_summary: ExecutiveSummary
    topics: List[TopicAnalysis]
    sources: List[Source] # Structured sources
