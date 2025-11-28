"""
Simple Stage 0 test - just verify it works
"""
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro")

test_text = "Zvýšíme důchody o 2000 Kč."

system_prompt = """Extract claims as JSON with: id, text, policy_area (pensions/healthcare/etc), claim_type (spending_increase_absolute/etc), target_entity, value_czk, value_percent, confidence. Return only JSON, no markdown."""

response = model.generate_content(
    f"{system_prompt}\n\nExtract from: {test_text}",
    generation_config=genai.types.GenerationConfig(temperature=0.2)
)

clean = response.text.replace("```json", "").replace("```", "").strip()
result = json.loads(clean)

print("RESULT:")
print(json.dumps(result, indent=2))

# Check structure
assert "claims" in result or isinstance(result, list)
print("\nPASSED: Stage 0 extraction works!")
