import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os
from dotenv import load_dotenv
load_dotenv()
from obb_utils import get_news

print(f"TIINGO_API_KEY present: {'TIINGO_API_KEY' in os.environ}")

symbol = "AAPL"
print(f"Fetching news for {symbol}...")
news = get_news(symbol, limit=5)

if news:
    print(f"Found {len(news)} news items.")
    for item in news:
        print(f"- [{item.get('source')}] {item.get('title')}")
else:
    print("No news found.")
