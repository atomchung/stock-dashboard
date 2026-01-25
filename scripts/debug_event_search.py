import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from duckduckgo_search import DDGS
import json

def test_search():
    ticker = "ONDS"
    print(f"--- Testing Targeted Web Search for {ticker} Calendars ---")
    
    # Try multiple query variations
    queries = [
        f"{ticker} next earnings date",
        f"{ticker} investor calendar upcoming events",
        f"{ticker} earnings call date marketbeat nasdaq"
    ]

    for q in queries:
        print(f"\nQuery: '{q}'")
        try:
            results = list(DDGS().text(keywords=q, region="us-en", safesearch="off", max_results=3))
            for res in results:
                print(f"- [{res.get('title')}]")
                print(f"  Snippet: {res.get('body')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
