import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import re

load_dotenv()

def clean_json_text(text):
    """Extract JSON from text that might have markdown fencing"""
    if not text:
        return text
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: No GEMINI_API_KEY found")
    exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

ticker = "ONDS"

prompt = f"""
Identify the top 4 public company competitors or industry peers for {ticker}.

IMPORTANT RULES:
1. Focus on companies in the SAME industry/sector with similar business models
2. Prefer companies with similar market cap size (small-cap with small-cap, large-cap with large-cap)
3. If no direct competitors exist, list companies in the same industry that investors would compare against
4. ONLY include publicly traded US stocks with valid ticker symbols
5. If you truly cannot find any relevant peers, return an empty list []

DO NOT list unrelated mega-cap tech stocks (AAPL, MSFT, GOOG, AMZN) unless they are actual direct competitors.

Return ONLY a valid JSON list of ticker symbols.
Example: ["TICKER1", "TICKER2", "TICKER3", "TICKER4"]
"""

print(f"Testing competitor identification for {ticker}...")
print("="*50)
print("Prompt sent:")
print(prompt)
print("="*50)

try:
    response = model.generate_content(prompt)
    raw_response = response.text
    print(f"\nRaw AI Response:")
    print(raw_response)
    print("="*50)
    
    cleaned = clean_json_text(raw_response)
    print(f"\nCleaned Response:")
    print(cleaned)
    print("="*50)
    
    result = json.loads(cleaned)
    print(f"\nParsed Result: {result}")
    print(f"Type: {type(result)}")
    
    if isinstance(result, list) and all(isinstance(t, str) for t in result):
        print(f"\n✅ SUCCESS: Found {len(result)} competitors: {result}")
    else:
        print(f"\n❌ INVALID: Result is not a list of strings")
        
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
