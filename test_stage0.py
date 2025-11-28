"""
Test script for Stage 0: Claim Extraction with strict schema.
Run this to verify the new extraction logic works before integrating.
"""

import json
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Fix console encoding for Czech characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
else:
    print("ERROR: No GEMINI_API_KEY found in .env")
    exit(1)

def extract_claims_strict(text: str) -> dict:
    """
    Extract claims with strict schema and low temperature.
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
    
    full_prompt = f"System Instruction: {system_prompt}\\n\\nUser Request: Extract claims from this text:\\n\\n{text}"
    
    # Use temperature 0.2 for consistency
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2
        )
    )
    
    # Parse response
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# Test cases
test_cases = [
    "Zvýšíme důchody o 2000 Kč.",
    "Snížíme DPH na potraviny na 10%.",
    "Zavedeme daň z tichého vína ve výši 5 Kč za litr.",
    "Zvýšíme výdaje na kulturu o 20%."
]

print("=" * 80)
print("STAGE 0 TEST: Strict Claim Extraction")
print("=" * 80)

for i, test_text in enumerate(test_cases, 1):
    print(f"\\n[TEST {i}] Input: {test_text}")
    print("-" * 80)
    
    try:
        result = extract_claims_strict(test_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Validate structure
        assert "claims" in result, "Missing 'claims' key"
        assert len(result["claims"]) > 0, "No claims extracted"
        
        for claim in result["claims"]:
            assert "id" in claim, "Missing 'id'"
            assert "text" in claim, "Missing 'text'"
            assert "policy_area" in claim, "Missing 'policy_area'"
            assert "claim_type" in claim, "Missing 'claim_type'"
            assert "target_entity" in claim, "Missing 'target_entity'"
            assert "confidence" in claim, "Missing 'confidence'"
        
        print("✓ PASSED")
        
    except Exception as e:
        print(f"✗ FAILED: {e}")

print("\\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
