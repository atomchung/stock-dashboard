
import requests
import json

def test_query(query_term):
    print(f"\n--- Testing Query: '{query_term}' ---")
    url = "https://gamma-api.polymarket.com/events"
    params = {
        "question": query_term,
        "limit": 5,
        "sort": "volume",
        "order": "desc",
        # "closed": "false" # Commenting out to see if closed markets appear
    }
    
    try:
        r = requests.get(url, params=params)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Count: {len(data)}")
            for i, event in enumerate(data):
                markets = event.get('markets', [])
                if not markets: continue
                # title = event.get('title')
                # volume = markets[0].get('volume')
                # slug = event.get('slug')
                # print(f"{i+1}. {title} | Vol: {volume} | Slug: {slug}")
                print(f"{i+1}. {json.dumps(event.get('title'), indent=2)}")
        else:
            print(r.text)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    test_query("AAPL")
    test_query("Apple")
