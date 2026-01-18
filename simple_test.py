import requests
import json

def check_public_search(term):
    url = "https://gamma-api.polymarket.com/public-search"
    params = {
        "q": term,
        "limit": 5,
        "type": "event" # Search for events
    }
    print(f"\n--- Testing /public-search: 'q={term}' ---")
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            print(f"Data Type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                 print(f"First Item Keys: {data[0].keys()}")
                 print(f"First Item Title: {data[0].get('title')}")
                 print(f"First Item Question: {data[0].get('question')}")
                 print(f"First Item Slug: {data[0].get('slug')}")
            else:
                 print(f"Raw Data Snippet: {str(data)[:1000]}")
        else:
            print(f"Error: {r.status_code} | {r.text}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_public_search("AAPL")
