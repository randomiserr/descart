import json
from typing import List, Dict, Any
import tools
from llm_client import LLMClient

class AdvisorOrchestrator:
    def __init__(self):
        self.llm = LLMClient()

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

        # 3. Synthesis
        print("3. Synthesizing Report...")
        report = self._synthesize_report(claims, context)
        print("   Report generated.")
        
        return report

    def _extract_claims(self, text: str) -> List[Dict]:
        """
        Uses LLM to parse text into structured claims.
        """
        system_prompt = """
        You are an expert political analyst. Your task is to extract specific, testable claims from political texts.
        For each claim, identify:
        - text: The exact claim text.
        - type: 'spending_increase', 'spending_cut', 'revenue_increase', 'revenue_decrease', 'regulatory_change', or 'general_policy'.
        - target: The specific entity, tax, or budget item involved (e.g., 'banks', 'VAT', 'renewable energy').
        - amount_claimed: Any specific numbers mentioned (e.g., '20 billion CZK').
        
        Return the output as a JSON list of objects.
        """
        
        response = self.llm.generate_response(f"Extract claims from this text:\n\n{text}", system_prompt)
        
        try:
            # Clean markdown code blocks if present
            clean_json = response.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            if isinstance(parsed, list):
                # Ensure all items are dicts
                validated_claims = []
                for item in parsed:
                    if isinstance(item, str):
                        validated_claims.append({"text": item, "type": "general_policy", "target": "unknown"})
                    elif isinstance(item, dict):
                        validated_claims.append(item)
                return validated_claims
            return [{"text": text, "type": "general_policy", "target": "unknown"}]
        except Exception as e:
            print(f"Error parsing LLM extraction: {e}")
            # Fallback to simple split
            return [{"text": text, "type": "general_policy", "target": "unknown"}]

    def _retrieve_context(self, claims: List[Dict]) -> Dict[str, Any]:
        """
        Calls tools based on claims.
        """
        context = {
            "budget_data": [],
            "legal_context": [],
            "macro_data": {},
            "web_search": []
        }

        for claim in claims:
            target = claim.get('target', '').lower()
            text = claim.get('text', '')
            
            # 1. Budget Search
            # Try to find relevant budget items
            budget_items = tools.get_budget(target)
            if not budget_items and "tax" in target:
                 # Try searching for "daň" if it's a tax
                 budget_items = tools.get_budget("daň")
            context['budget_data'].extend(budget_items)
            
            # 2. Legal Search
            # Search for laws related to the target
            laws = tools.get_law_context(target)
            context['legal_context'].extend(laws)
            
            # 3. Macro Data
            # If it's a big fiscal claim, get GDP/Inflation context
            context['macro_data'] = tools.get_macro_snapshot(["GDP", "Inflation"])

            # 4. Web Search (New)
            # Search for recent news/debates about this topic
            # Use Czech keywords for better local results
            search_query = f"{text} diskuze názory experti"
            web_results = tools.search_web(search_query, max_results=3)
            context['web_search'].extend(web_results)

        return context

    def _synthesize_report(self, claims: List[Dict], context: Dict) -> Dict:
        """
        Synthesizes the final report using LLM.
        """
        system_prompt = """
        Jste přísný, nestranný ekonomický poradce. Analyzujte proveditelnost a dopady následujících politických tvrzení na základě poskytnutých dat.
        
        Výstup musí být v ČEŠTINĚ.
        
        DŮLEŽITÉ PRAVIDLO PRO ZDROJE:
        - Zdroje uvádějte PŘÍMO v textu analýzy tam, kde je to relevantní.
        - Použijte speciální značku: <cite source='Název Zdroje'>text, který zdroj dokládá</cite>.
        - Příklad: "Podle zákona je <cite source='Zákon o DPH'>sazba 21%</cite>, což znamená..."
        - NIKDY neodkazujte na "LEGAL CONTEXT", "BUDGET DATA", "MACRO CONTEXT", "Rozpočtová data", "Analýza rozpočtu" atd.
        - Pokud nemáte konkrétní zdroj (např. pro obecný výpočet dopadu), použijte zdroj 'Modelový výpočet' nebo 'Expertní odhad'.
        - Pokud data chybí, NEUVÁDĚJTE žádný zdroj, prostě napište, že data nejsou k dispozici.
        - POZOR: Protože výstup je JSON, ujistěte se, že uvozovky uvnitř stringu jsou správně ošetřeny (escaped), nebo použijte jednoduché uvozovky pro atributy tagů.
        
        Postup:
        1. Seskupte tvrzení do logických témat.
        2. Pro každé téma napište 'overall_analysis' a 'future_impact'.
        3. Pro každé tvrzení v tématu proveďte detailní analýzu (Feasibility, Fiscal Impact, Risks, Public Opinion).
           - V KAŽDÉ sekci používejte <cite> tagy pro ozdrojování konkrétních faktů.
           - Pokud nalezený právní kontext (LEGAL CONTEXT) není relevantní k tématu, NEZMIŇUJTE HO a necitujte ho. Napište, že relevantní legislativa nebyla v kontextu nalezena.
           - U fiskálního dopadu se snažte o konkrétní vyčíslení (např. počet lidí * částka). Pokud to děláte sami, VŽDY to ozdrojujte jako <cite source='Modelový výpočet'>...</cite>.
        
        Formát výstupu (JSON):
        {
          "topics": [
            {
              "name": "Název Tématu",
              "overall_analysis": "Text...",
              "future_impact": "Text...",
              "claims": [
                {
                  "text": "Původní text tvrzení",
                  "feasibility": "Text s <cite source='...'>tagy</cite>...",
                  "fiscal_impact": "Text s <cite source='...'>tagy</cite>...",
                  "legal_risks": "Text s <cite source='...'>tagy</cite>...",
                  "public_expert_opinion": "Text..."
                }
              ]
            }
          ]
        }
        """
        
        # Prepare context summary for the prompt
        budget_summary = json.dumps(context['budget_data'][:15], indent=2, ensure_ascii=False) 
        legal_summary = "\n".join([f"- {l['source_document']}: {l['content_chunk'][:300]}..." for l in context['legal_context'][:5]])
        macro_summary = json.dumps(context['macro_data'], indent=2, ensure_ascii=False)
        web_summary = "\n".join([f"- {w['title']} ({w['source']}): {w['snippet']}" for w in context['web_search']])
        
        prompt = f"""
        TVRZENÍ (CLAIMS):
        {json.dumps(claims, indent=2, ensure_ascii=False)}
        
        ROZPOČET 2025 (BUDGET DATA):
        {budget_summary}
        
        PRÁVNÍ KONTEXT (LEGAL CONTEXT):
        {legal_summary}
        
        MAKROEKONOMICKÁ DATA (MACRO CONTEXT):
        {macro_summary}
        
        WEB SEARCH (NÁZORY/ZPRÁVY):
        {web_summary}
        
        Generujte analýzu v JSON.
        """
        
        response = self.llm.generate_response(prompt, system_prompt)
        
        try:
            clean_json = response.replace("```json", "").replace("```", "").strip()
            report = json.loads(clean_json)
            return self._sanitize_report(report)
        except Exception as e:
            print(f"Error parsing LLM synthesis: {e}")
            return {"error": "Failed to generate report", "raw_response": response}

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
        """
        # 1. Extract Claims
        claims = self._extract_claims(text)
        
        # 2. Retrieve Context
        context = self._retrieve_context(claims)
        
        # 3. Synthesize Report
        report = self._synthesize_report(claims, context)
        
        # Merge context into report for debugging/display
        report['debug_context'] = context
        return report

