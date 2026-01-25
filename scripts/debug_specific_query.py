import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from duckduckgo_search import DDGS

def test_specific():
    ticker = "ONDS"
    # Simplified query
    query = f"{ticker} next earnings date upcoming events"
    print(f"Testing Query: '{query}'")
    
    try:
        results = list(DDGS().text(keywords=query, region="us-en", safesearch="off", max_results=4))
        print(f"Results found: {len(results)}")
        for r in results:
            print(f"- {r.get('title')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_specific()
