import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
"""
Verify Migration Script
Tests if utils.py correctly fetches data via OpenBB/obb_utils.
"""
import utils
import sys

def verify_migration():
    print("--- Verifying Utils Migration to OpenBB ---")
    
    ticker = "AAPL"
    
    # 1. Test get_stock_data
    print(f"\n1. Testing get_stock_data('{ticker}')...")
    try:
        t, err = utils.get_stock_data(ticker)
        if err:
            print(f"FAILED: {err}")
        else:
            info = t.info
            print(f"SUCCESS! Name: {info.get('shortName')}, Market Cap: {info.get('marketCap')}")
            # Verify it's not empty
            if not info.get('shortName'):
                print("WARNING: shortName is empty. Check OpenBB mapping.")
    except Exception as e:
        print(f"EXCEPTION: {e}")

    # 2. Test get_news
    print(f"\n2. Testing get_news('{ticker}')...")
    try:
        news = utils.get_news(ticker)
        print(f"SUCCESS! Fetched {len(news)} news items.")
        if len(news) > 0:
            print(f"Sample: {news[0].get('title')} ({news[0].get('source')})")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        
    # 3. Test get_historical_data
    print(f"\n3. Testing get_historical_data('{ticker}')...")
    try:
        df = utils.get_historical_data(ticker, period="5d")
        print(f"SUCCESS! Fetched {len(df)} rows.")
        print(df.tail())
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    verify_migration()
