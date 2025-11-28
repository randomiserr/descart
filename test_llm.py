import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

def test_model(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Hello, are you working?"}]}]
    }
    
    print(f"Testing model: {model_name}...")
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("SUCCESS!")
            print(response.json()['candidates'][0]['content']['parts'][0]['text'])
            return True
        else:
            print(f"FAILED: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if not API_KEY:
        print("No API Key found in .env")
    else:
        # Try a few common models
        models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]
        for m in models:
            if test_model(m):
                break
