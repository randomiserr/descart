import json
from typing import List, Dict, Any
import tools
from llm_client import LLMClient
from retrieval import DeterministicRetrieval
from calculations import CalculationEngine

class AdvisorOrchestrator:
    def __init__(self):
        self.llm = LLMClient()
        self.retrieval = DeterministicRetrieval()
        self.calc_engine = CalculationEngine()

    def analyze_plan(self, plan_text: str) -> Dict[str, Any]:
        """
        Main entry point: Analyze a political plan.
        """
        print(f"--- Analyzing Plan: {plan_text[:50]}... ---")
        
        # 1. Claim Extraction
        print("1. Extracting Claims...")
        claims = self._extract_claims(plan_text)
        print(f"   Extracted {len(claims)} claims.")

        # 2. Fact Retrieval
        print("2. Retrieving Context...")
        context = self._retrieve_context(claims)
        print("   Context retrieved.")

        # 3. Calculations
        print("3. Running Calculations...")
        results = []
        for claim, facts in zip(claims, context['facts']):
            result = self.calc_engine.calculate(claim, facts)
            results.append(result)
        print(f"   Calculated {len(results)} results.")
        
        # Log unsupported claims if any
        if self.calc_engine.unsupported_log:
            self._log_unsupported_claims(self.calc_engine.unsupported_log)

        # 4. Synthesis
        print("4. Synthesizing Report...")
        report = self._synthesize_report(claims, context, results)
        print("   Report generated.")
        
        # Serialize calculations for frontend
        # Map claim_id to calculation result
        calculations_map = {}
        for claim, res in zip(claims, results):
            if claim.get("id"):
                calculations_map[claim["id"]] = res.dict()
        
        return {
            "report": report,
            "calculations": calculations_map,
            "debug_context": context
        }
    
    def _log_unsupported_claims(self, unsupported: List[Dict]):
        """Write unsupported claims to a log file."""
        import os
        import datetime
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"unsupported_claims_{timestamp}.json")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(unsupported, f, ensure_ascii=False, indent=2)
        
        print(f"   Logged {len(unsupported)} unsupported claims to {log_file}")

    def _extract_claims(self, text: str) -> List[Dict]:
        """
        Uses LLM to parse text into structured claims with strict schema.
        Temperature: 0.2 for consistency.
        """
        system_prompt = """
        You are an expert political analyst. Extract specific, testable claims from Czech political texts.
        
        For each claim, identify:
        - id: Unique ID (C1, C2, C3...)
        - text: Exact claim text in Czech
        - policy_area: One of: pensions, healthcare, education, culture, defense, infrastructure, 
                       social_services, taxation, environment, agriculture, justice, public_admin, other
        - claim_type: One of:
            * spending_increase_absolute (e.g., "Zvýšíme důchody o 2000 Kč")
            * spending_increase_percent (e.g., "Zvýšíme výdaje o 10%")
            * spending_cut_absolute
            * spending_cut_percent
            * tax_rate_increase (e.g., "Zvýšíme DPH na 25%")
            * tax_rate_decrease
            * tax_base_change (e.g., "Zavedeme novou daň")
            * regulatory_change
            * general_policy
        - target_entity: Specific entity (e.g., "state_pensions", "VAT", "culture_subsidies")
        - value_czk: Amount in CZK if mentioned (null if not)
        - value_percent: Percentage if mentioned (null if not)
        - confidence: 0.0-1.0 (how confident you are in the extraction)
        
        Return ONLY valid JSON matching this schema. No markdown, no explanations.
        
        Example output:
        {
          "claims": [
            {
              "id": "C1",
              "text": "Zvýšíme důchody o 2000 Kč",
              "policy_area": "pensions",
              "claim_type": "spending_increase_absolute",
              "target_entity": "state_pensions",
              "value_czk": 2000,
              "value_percent": null,
              "confidence": 1.0
            }
          ]
        }
        """
        
        response = self.llm.generate_response(
            f"Extract claims from this text:\n\n{text}", 
            system_prompt,
            temperature=0.2  # Low temperature for consistency
        )
        
        try:
            # Clean markdown code blocks if present
            clean_json = response.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            
            # Handle both {"claims": [...]} and direct list formats
            if isinstance(parsed, dict) and "claims" in parsed:
                claims_list = parsed["claims"]
            elif isinstance(parsed, list):
                claims_list = parsed
            else:
                claims_list = [parsed]
            
            # Validate and convert to old format for compatibility
            validated_claims = []
            for claim in claims_list:
                if isinstance(claim, dict):
                    # Keep new fields but also add old 'target' field for compatibility
                    claim['target'] = claim.get('target_entity', 'unknown')
                    claim['type'] = claim.get('claim_type', 'general_policy')
                    validated_claims.append(claim)
            
            return validated_claims if validated_claims else [{
                "id": "C1",
                "text": text,
                "policy_area": "other",
                "claim_type": "general_policy",
                "target_entity": "unknown",
                "target": "unknown",
                "type": "general_policy",
                "value_czk": None,
                "value_percent": None,
                "confidence": 0.5
            }]
            
        except Exception as e:
            print(f"Error parsing LLM extraction: {e}")
            print(f"Raw response: {response[:500]}")
            # Fallback
            return [{
                "id": "C1",
                "text": text,
                "policy_area": "other",
                "claim_type": "general_policy",
                "target_entity": "unknown",
                "target": "unknown",
                "type": "general_policy",
                "value_czk": None,
                "value_percent": None,
                "confidence": 0.5
            }]

    def _retrieve_context(self, claims: List[Dict]) -> Dict[str, Any]:
        """
        Deterministic context retrieval using fixed mappings.
        """
        all_facts = []
        
        for claim in claims:
            facts = self.retrieval.retrieve_facts(claim)
            all_facts.append(facts)
        
        # Aggregate for backward compatibility and LLM context
        context = {
            "budget_data": [],
            "legal_context": [],  # Empty for now (simplified in Stage 1 refactor)
            "macro_data": {},
            "web_search": [],
            "facts": all_facts  # New structured facts
        }
        
        # Flatten facts for the legacy context structure (used in prompt)
        for facts in all_facts:
            if "budget" in facts and "line_items" in facts["budget"]:
                context["budget_data"].extend(facts["budget"]["line_items"])
            
            # Laws removed in Stage 1 simplification - can add back if needed
            # if "laws" in facts:
            #     context["legal_context"].extend(facts["laws"])
            
            if "macro" in facts and facts["macro"]:
                context["macro_data"] = facts["macro"]
            
            if "web_search" in facts:
                context["web_search"].extend(facts["web_search"])
        
        return context

    def _synthesize_report(self, claims: List[Dict], context: Dict, calculation_results: List[Any] = None) -> Dict:
        """
        Stage 3: LLM Explanation (Pure Synthesis, No Calculation)
        Temperature: 0.2 for factuality
        """
        # Format calculation results prominently in the prompt
        calc_section = self._format_calculations_for_prompt(claims, calculation_results)
        
        # Build source registry
        source_registry = self._build_source_registry(context)
        
        system_prompt = f"""
        Jste přísný, nestranný ekonomický poradce. Analyzujte proveditelnost a dopady politických tvrzení.
        
        🔴 KRITICKÁ PRAVIDLA:
        1. NIKDY nevymýšlejte čísla. Pokud není číslo v "MODELOVÉ VÝPOČTY", v poli "quantitative" uveďte null.
        2. VŽDY poskytněte kvalitativní hodnocení ("qualitative"), i když chybí data pro výpočet.
        3. Vyberte 3-5 nejrelevantnějších dimenzí pro každé tvrzení z tohoto seznamu:
           - fiscal (Fiskální dopad)
           - feasibility (Proveditelnost)
           - legal (Právní rizika)
           - public_opinion (Veřejné mínění & experti)
           - eu_alignment (Soulad s EU)
           - structural (Strukturální/Ekonomické dopady)
           - social (Sociální dopady)
           - environment (Environmentální dopady)
        
        CITACE ZDROJŮ:
        - V textu používejte: <cite source='Název Zdroje'>citovaný text</cite>
        - Dostupné zdroje:
{self._format_source_list(source_registry)}
        - Pro modelové výpočty: <cite source='Modelový výpočet'>text</cite>
        - WEBOVÉ ZDROJE jsou validní kontext pro kvalitativní hodnocení.
        
        MODELOVÉ VÝPOČTY (POUŽIJTE PRO KVANTITATIVNÍ DATA):
{calc_section}
        
        Formát výstupu (JSON):
        {{
          "topics": [
            {{
              "name": "Název Tématu",
              "overall_analysis": "Stručné shrnutí tématu...",
              "claims": [
                {{
                  "claim_id": "ID tvrzení",
                  "text": "Text tvrzení",
                  "analysis": [
                    {{
                      "dimension": "fiscal | feasibility | legal | public_opinion | eu_alignment | structural | social | environment",
                      "title": "Název dimenze (např. Fiskální dopad)",
                      "quantitative": {{
                        "status": "not_modelled | modelled | insufficient_data",
                        "amount_czk": 123456 (nebo null),
                        "confidence": 0.0 (0.0-1.0)
                      }},
                      "qualitative": {{
                        "status": "supported | speculative | unknown",
                        "summary": "Detailní kvalitativní rozbor. Pokud chybí data, vysvětlete co lze odvodit z kontextu (EU trendy, ekonomická teorie atd.).",
                        "evidence": ["source_id_1", "web_search_1"]
                      }}
                    }}
                  ]
                }}
              ]
            }}
          ]
        }}
        """
        
        # Prepare minimal context
        prompt = f"""
        TVRZENÍ K ANALÝZE:
        {json.dumps(claims, indent=2, ensure_ascii=False)}
        
        DOSTUPNÉ ZDROJE:
{self._format_context_for_prompt(context, source_registry)}
        
        Vygenerujte analýzu v JSON formátu. Pro každé tvrzení vyberte relevantní dimenze.
        """
        
        # **Stage 3: Lower Temperature = 0.2**
        response = self.llm.generate_response(prompt, system_prompt, temperature=0.2)
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            report = json.loads(clean_json)
            return self._sanitize_report(report)
        except Exception as e:
            print(f"Error parsing LLM synthesis: {e}")
            return {"error": "Failed to generate report", "raw_response": response}
    
    def _format_calculations_for_prompt(self, claims: List[Dict], results: List[Any]) -> str:
        """Format calculation results for the LLM prompt."""
        if not results:
            return "(Žádné výpočty k dispozici)"
        
        lines = []
        for i, (claim, res) in enumerate(zip(claims, results)):
            if res.confidence > 0:
                claim_text = claim.get("text", "Unknown")[:60]
                lines.append(f"\n[Claim {i+1}] \"{claim_text}...\"")
                
                if res.cost_czk:
                    lines.append(f"  → NÁKLAD: {res.cost_czk:,.0f} CZK")
                if res.revenue_czk:
                    lines.append(f"  → PŘÍJEM: {res.revenue_czk:,.0f} CZK")
                    
                lines.append(f"  → Formule: {res.formula_used}")
                lines.append(f"  → Předpoklady: {', '.join(res.assumptions)}")
            else:
                lines.append(f"\n[Claim {i+1}] Výpočet není k dispozici (důvod: {', '.join(res.assumptions)})")
        
        return "\n".join(lines)
    
    def _build_source_registry(self, context: Dict) -> Dict[str, str]:
        """Build a registry of all available sources."""
        registry = {}
        
        # Add sources from facts (if they have source_id)
        for fact_set in context.get('facts', []):
            if 'sources' in fact_set:
                registry.update(fact_set['sources'])
        
        return registry
    
    def _format_source_list(self, registry: Dict[str, str]) -> str:
        """Format source registry as a list."""
        if not registry:
            return "        (Žádné specifické zdroje)"
        
        lines = []
        for source_id, source_name in list(registry.items())[:10]:  # Limit to 10 for brevity
            lines.append(f"        - {source_id}: {source_name}")
        
        if len(registry) > 10:
            lines.append(f"        ... a {len(registry) - 10} dalších zdrojů")
        
        return "\n".join(lines)
    
    def _format_context_for_prompt(self, context: Dict, registry: Dict) -> str:
        """Format context as a concise summary, not raw data dumps."""
        lines = []
        
        # Budget summary (just totals, not full items)
        if context.get('budget_data'):
            total = sum(item.get('amount_czk', 0) for item in context['budget_data'])
            lines.append(f"- Rozpočtové kapitoly: {len(context['budget_data'])} položek, celkem {total:,.0f} CZK")
        
        # Legal summary (just titles)
        if context.get('legal_context'):
            laws = [l.get('source_document', 'Zákon') for l in context['legal_context'][:3]]
            lines.append(f"- Právní kontext: {', '.join(laws)}")
        
        # Web summary (include snippets)
        if context.get('web_search'):
            lines.append(f"\nWEBOVÉ ZDROJE (Aktuální kontext):")
            for i, result in enumerate(context['web_search'][:3]): # Top 3 results
                source_id = result.get('source_id', f'web_{i}')
                title = result.get('title', 'Unknown')
                snippet = result.get('snippet', '')[:300] # Limit snippet length
                lines.append(f"- [{source_id}] {title}: \"{snippet}...\"")
        
        lines.append(f"\nVšechny detaily jsou dostupné přes source_id v registru zdrojů.")
        
        return "\n".join(lines)

    def _sanitize_report(self, data: Any) -> Any:
        """
        Recursively sanitizes the report to remove forbidden source names.
        """
        forbidden = [
            "LEGAL CONTEXT", "BUDGET DATA", "MACRO CONTEXT", 
            "Rozpočtová data", "Analýza rozpočtu", "MAKROEKONOMICKÁ DATA",
            "WEB SEARCH", "NÁZORY"
        ]
        
        if isinstance(data, dict):
            return {k: self._sanitize_report(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_report(item) for item in data]
        elif isinstance(data, str):
            # Regex to find cite tags
            import re
            def replace_source(match):
                source = match.group(1)
                content = match.group(2)
                
                # Check if source contains any forbidden term (case insensitive)
                for term in forbidden:
                    if term.lower() in source.lower():
                        # If forbidden, just return the content without the tag
                        # Or replace with generic if it looks like a calculation
                        if "výpočet" in content.lower() or "miliard" in content.lower():
                             return f"<cite source='Modelový výpočet'>{content}</cite>"
                        return content
                
                return match.group(0)

            # Replace <cite source='...'>...</cite>
            # Handle both single and double quotes
            pattern = r"<cite source=['\"]([^'\"]+)['\"]>(.*?)</cite>"
            return re.sub(pattern, replace_source, data, flags=re.DOTALL)
            
        return data

    def process_request(self, text: str) -> Dict:
        """
        Public entry point for the Streamlit app.
        Wraps analyze_plan to maintain backward compatibility.
        """
        # Call the main analysis pipeline
        result = self.analyze_plan(text)
        
        # Extract report
        report = result["report"]
        
        # Add calculations to the report structure if possible, or just ignore for now
        # Streamlit app expects just the report dict
        
        # We can try to inject calculations into the report if needed, 
        # but for now let's just return the report as Streamlit expects.
        # The LLM has already incorporated calculation results into the text 
        # (via <cite source='Modelový výpočet'> tags).
        
        # Re-construct debug context
        if "debug_context" in result:
             report['debug_context'] = result["debug_context"]
        
        return report

