
from duckduckgo_search import DDGS
import json

def test_search(ticker):
    query = f"{ticker} financial results analysis revenue profit drivers"
    print(f"Searching for: {query}")
    results = list(DDGS().news(keywords=query, region="us-en", safesearch="off", timelimit="y", max_results=5))
    for i, r in enumerate(results):
        print(f"--- Result {i+1} ---")
        print(f"Title: {r.get('title')}")
        print(f"Body: {r.get('body')}")
        print(f"URL: {r.get('url')}")
        print("-" * 20)

if __name__ == "__main__":
    test_search("CAVA")
