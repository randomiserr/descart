import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMClient:
    def __init__(self, provider="gemini", model="gemini-flash-latest"):
        self.provider = provider
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.genai_model = genai.GenerativeModel(self.model)
        else:
            self.genai_model = None

    def generate_response(self, prompt: str, system_instruction: str = None, temperature: float = 0.7) -> str:
        """
        Generates a response from the LLM.
        """
        if not self.genai_model:
            print("WARNING: No API Key found. Returning mock response.")
            return self._mock_response(prompt)

        if self.provider == "gemini":
            return self._call_gemini(prompt, system_instruction, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_gemini(self, prompt: str, system_instruction: str, temperature: float = 0.7) -> str:
        """
        Calls Google Gemini via SDK.
        """
        try:
            # Combine system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System Instruction: {system_instruction}\\n\\nUser Request: {prompt}"
            
            # Use generation config for temperature
            response = self.genai_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )
            return response.text
        except Exception as e:
            print(f"LLM API Error: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Fallback mock response if no API key.
        """
        if "extract claims" in prompt.lower():
            return json.dumps({
                "claims": [{
                    "id": "C1",
                    "text": prompt[:100],
                    "policy_area": "other",
                    "claim_type": "general_policy",
                    "target_entity": "unknown",
                    "value_czk": None,
                    "value_percent": None,
                    "confidence": 0.5
                }]
            })
        return "Mock LLM Response: I analyzed your input."
