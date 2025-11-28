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

    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates a response from the LLM.
        """
        if not self.genai_model:
            print("WARNING: No API Key found. Returning mock response.")
            return self._mock_response(prompt)

        if self.provider == "gemini":
            return self._call_gemini(prompt, system_instruction)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        """
        Calls Google Gemini via SDK.
        """
        try:
            # Combine system instruction if provided (SDK supports it in init, but we are reusing the object)
            # For simplicity, we'll prepend it to the prompt as before, or use the generate_content argument if supported dynamically
            # The safest way for a single model instance is to prepend.
            
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System Instruction: {system_instruction}\n\nUser Request: {prompt}"
            
            response = self.genai_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"LLM API Error: {e}")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Fallback mock response if no API key.
        """
        if "extract claims" in prompt.lower():
            return json.dumps([{
                "id": "mock_claim_1",
                "text": "Extracted Claim: " + prompt[:50],
                "type": "general_policy",
                "target": "unknown"
            }])
        return "Mock LLM Response: I analyzed your input."

    def _mock_response(self, prompt: str) -> str:
        """
        Fallback mock response if no API key.
        """
        if "extract claims" in prompt.lower():
            return json.dumps([{
                "id": "mock_claim_1",
                "text": "Extracted Claim: " + prompt[:50],
                "type": "general_policy",
                "target": "unknown"
            }])
        return "Mock LLM Response: I analyzed your input."
