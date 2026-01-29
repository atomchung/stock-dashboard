
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API Key found")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    print(f"Querying: {url.replace(api_key, 'HIDDEN')}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nAvailable Models:")
            for m in data.get('models', []):
                print(f"- {m['name']} ({m.get('displayName')})")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_models()
