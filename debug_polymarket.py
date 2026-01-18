
import requests
import json

def test_query(query_term):
    print(f"\n--- Testing Query: '{query_term}' ---")
    
    # Test 1: Events with 'q' (Hypothesis)
    print("Test 1: /events with 'q'")
    url = "https://gamma-api.polymarket.com/events"
    params = {"q": query_term, "limit": 5, "closed": "false"}
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            print(f"Results: {len(data)}")
            if len(data) > 0: print(f"Sample: {data[0].get('title')}")
        else:
            print(f"Status: {r.status_code}")
    except Exception as e:
        print(e)

    # Test 2: Public Search (Documented)
    print("\nTest 2: /public-search")
    url_search = "https://gamma-api.polymarket.com/public-search"
    params_search = {"q": query_term, "limit": 5, "type": "event"} # 'type' might be needed
    try:
        r = requests.get(url_search, params=params_search)
        if r.status_code == 200:
            data = r.json()
            # public-search often returns a list or a dict
            print(f"Results type: {type(data)}")
            if isinstance(data, list):
                print(f"Count: {len(data)}")
                for item in data[:3]:
                     print(f"- {item.get('title', 'No Title')} ({item.get('slug')})")
            else:
                 print(data)
        else:
            print(f"Status: {r.status_code} | {r.text[:200]}")
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    test_query("AAPL")
    test_query("Apple")
