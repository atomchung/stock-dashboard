import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from GoogleNews import GoogleNews

def test_news():
    print("Testing GoogleNews...")
    try:
        googlenews = GoogleNews(lang='en', region='US')
        googlenews.get_news("AAPL stock")
        results = googlenews.results()
        print(f"Results count: {len(results)}")
        if results:
            print(results[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_news()
