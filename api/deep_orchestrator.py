import json
import os
import asyncio
import hashlib
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from models import (
    ExtractionResult, PlanningResult, ResearchResults, HardData, PlanAnalysis,
    Topic, TopicQueries, TavilyResult, ExecutiveSummary, TopicAnalysis, DimensionAssessment, Source
)
from prompts import EXTRACTION_SYSTEM_PROMPT, ANALYST_SYSTEM_PROMPT
from llm_client import LLMClient
from retrieval import DeterministicRetrieval
from calculations import CalculationEngine
import tools

load_dotenv()

CACHE_DIR = "data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class DeepResearchOrchestrator:
    def __init__(self):
        # Use single model for simplicity as requested
        # Using gemini-flash-latest for speed and reliability
        self.extraction_llm = LLMClient(model="gemini-flash-latest")
        self.analysis_llm = LLMClient(model="gemini-flash-latest")
        
        self.retrieval = DeterministicRetrieval()
        self.calc_engine = CalculationEngine()
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    def _get_cache_path(self, text: str) -> str:
        hash_md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        return os.path.join(CACHE_DIR, f"{hash_md5}.json")

    def _check_cache(self, text: str) -> Optional[Dict[str, Any]]:
        path = self._get_cache_path(text)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CACHE] Error reading cache: {e}")
        return None

    def _save_cache(self, text: str, data: Dict[str, Any]):
        path = self._get_cache_path(text)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CACHE] Error saving cache: {e}")

    async def run_pipeline(self, raw_text: str) -> Dict[str, Any]:
        print(f"--- Starting Political Agent Pipeline ---")
        
        # 0. Check Cache
        cached = self._check_cache(raw_text)
        if cached:
            print(f"[CACHE] Hit! Returning cached result.")
            return cached

        # 1. Extraction (Topics)
        print("1. Extraction Stage (Topics)...")
        extracted = await self.run_extraction(raw_text)
        print(f"   Extracted {len(extracted.topics)} topics.")
        
        # 2. Planning
        print("2. Planning Stage...")
        planning = await self.run_planning(raw_text, extracted)
        print(f"   Planning Mode: {planning.mode}")
        
        # 3. Research
        print("3. Research Stage...")
        # Pass extracted to run_research to use the initial queries
        research_results = await self.run_research(planning, extracted)
        print(f"   Gathered research for {len(research_results.by_topic)} topics.")
        
        # 4. Hard Data & Calculations
        print("4. Hard Data & Calculations Stage...")
        hard_data = await self.run_hard_data(extracted)
        print("   Hard data retrieved and calculations performed.")
        
        # 5. Analysis
        print("5. Analysis Stage...")
        analysis = await self.run_analysis(raw_text, extracted, hard_data, research_results)
        print("   Analysis complete.")
        
        result_dict = analysis.dict()
        
        # Save to cache
        self._save_cache(raw_text, result_dict)
        
        return result_dict

    async def run_extraction(self, raw_text: str) -> ExtractionResult:
        prompt = json.dumps({"raw_text": raw_text}, ensure_ascii=False)
        print(f"[EXTRACTION] Calling LLM with prompt length: {len(prompt)}")
        response = self.extraction_llm.generate_response(prompt, system_instruction=EXTRACTION_SYSTEM_PROMPT, temperature=0.2)
        
        try:
            # Clean response
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            result = ExtractionResult(**data)
            return result
        except Exception as e:
            print(f"[EXTRACTION] Error: {e}")
            print(f"[EXTRACTION] Full response: {response}")
            # Fallback
            return ExtractionResult(topics=[], research_queries=[])

    async def run_planning(self, raw_text: str, extracted: ExtractionResult) -> PlanningResult:
        # Prepare input for Planning Mode
        input_data = {
            "raw_text": raw_text,
            "topics": [t.dict() for t in extracted.topics],
            "hard_data": {},
            "research_results": [] # Empty triggers Planning Mode
        }
        
        prompt = json.dumps(input_data, ensure_ascii=False)
        response = self.analysis_llm.generate_response(prompt, system_instruction=ANALYST_SYSTEM_PROMPT, temperature=0.2)
        
        try:
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            return PlanningResult(**data)
        except Exception as e:
            print(f"Planning Error: {e}")
            return PlanningResult(mode="planning", additional_queries=[])

    async def run_research(self, planning: PlanningResult, extracted: ExtractionResult) -> ResearchResults:
        results_map = {}
        
        # 1. Use queries from Extraction Stage
        if extracted.research_queries:
            for item in extracted.research_queries:
                # Handle both dict and object access if Pydantic model
                if isinstance(item, dict):
                    topic_id = item.get("topic_id")
                    queries = item.get("queries", [])
                else:
                    topic_id = item.topic_id
                    queries = item.queries
                
                if topic_id not in results_map:
                    results_map[topic_id] = []
                
                for query in queries:
                    print(f"   [Research] Searching: {query}")
                    search_res = tools.search_tavily(query, max_results=3)
                    tavily_result = TavilyResult(query=query, results=search_res)
                    results_map[topic_id].append(tavily_result)

        # 2. Use additional queries from Planning Stage
        if planning.additional_queries:
            for topic_queries in planning.additional_queries:
                topic_id = topic_queries.topic_id
                if topic_id not in results_map:
                    results_map[topic_id] = []
                
                for query in topic_queries.queries:
                    print(f"   [Research] Additional Search: {query}")
                    search_res = tools.search_tavily(query, max_results=3)
                    tavily_result = TavilyResult(query=query, results=search_res)
                    results_map[topic_id].append(tavily_result)
        
        return ResearchResults(by_topic=results_map)

    async def run_hard_data(self, extracted: ExtractionResult) -> HardData:
        # Adapt topics to "claims" structure for existing retrieval logic
        # This is a compatibility bridge
        
        all_facts = []
        calc_results_map = {}
        
        for topic in extracted.topics:
            # Create a synthetic "claim" for retrieval
            synthetic_claim = {
                "id": topic.id,
                "text": topic.name + ": " + topic.description,
                "domain": topic.category,
                "policy_type": "topic_analysis"
            }
            
            # Retrieve facts
            facts = self.retrieval.retrieve_facts(synthetic_claim)
            all_facts.append(facts)
            
            # Run calculations (if applicable)
            # We treat the topic description as the "text" for calculation extraction
            calc_res = self.calc_engine.calculate(synthetic_claim, facts)
            if topic.id:
                calc_results_map[topic.id] = calc_res.dict()
        
        # Aggregate context for HardData
        global_budget = []
        global_macro = {}
        
        for facts in all_facts:
            if facts.get("budget"):
                global_budget.extend(facts["budget"])
            if facts.get("macro"):
                global_macro.update(facts["macro"])
        
        hard_data = HardData(
            laws={"items": []}, 
            budget={"items": global_budget},
            macro={"items": global_macro},
            calc_results=calc_results_map
        )
        
        return hard_data

    async def run_analysis(self, raw_text: str, extracted: ExtractionResult, hard_data: HardData, research_results: ResearchResults) -> PlanAnalysis:
        # Prepare input for Analysis Mode
        
        # Flatten research results
        all_tavily_results = []
        for results_list in research_results.by_topic.values():
            for res in results_list:
                all_tavily_results.append(res.dict())

        input_data = {
            "raw_text": raw_text,
            "topics": [t.dict() for t in extracted.topics],
            "hard_data": hard_data.dict(),
            "research_results": all_tavily_results
        }
        
        prompt = json.dumps(input_data, ensure_ascii=False)
        response = self.analysis_llm.generate_response(prompt, system_instruction=ANALYST_SYSTEM_PROMPT, temperature=0.2)
        
        try:
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            
            # Create Source objects from research results
            sources = []
            source_id = 1
            
            # Add Tavily/DuckDuckGo sources
            for tavily_result in all_tavily_results:
                for result in tavily_result.get("results", []):
                    if result.get("link") or result.get("snippet"):
                        sources.append(Source(
                            id=str(source_id),
                            name=result.get("title", f"Web Source {source_id}"),
                            url=result.get("link")
                        ))
                        source_id += 1
            
            # Add sources to the data if not already present
            if "sources" not in data or not data["sources"]:
                data["sources"] = [s.dict() for s in sources]
            
            return PlanAnalysis(**data)
        except Exception as e:
            print(f"Analysis Error: {e}")
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(f"Error: {e}\n")
                f.write(f"Response preview: {response}\n")
                import traceback
                traceback.print_exc(file=f)
            
            # Return error result
            return PlanAnalysis(
                mode="analysis",
                executive_summary=ExecutiveSummary(
                    plan_name="Chyba analýzy",
                    overview_cs=f"Nepodařilo se dokončit analýzu. Error: {str(e)[:200]}",
                    main_benefits=[],
                    main_risks=[],
                    strategic_verdict_2035="N/A",
                    recommendations=[]
                ),
                topics=[],
                sources=[]
            )

