import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from openbb import obb
import pandas as pd

def test_openbb_light():
    symbol = "AAPL"
    print(f"--- Testing OpenBB Light with Symbol: {symbol} ---")

    # 1. Fetch Historical Price
    print("\n1. Fetching Historical Price (Provider: yfinance)...")
    try:
        # Note: In OpenBB v4, output is an OBBject. .results is usually a list of models or a DataFrame depending on usage.
        # obb.equity.price.historical returns a list of models by default, need to convert to dataframe or use direct access
        price_data = obb.equity.price.historical(symbol=symbol, provider="yfinance", limit=5)
        df_price = price_data.to_df()
        print("Success!")
        print(df_price.head())
    except Exception as e:
        print(f"FAILED to fetch price: {e}")

    # 2. Fetch Company Profile/Info
    print("\n2. Fetching Company Info (Provider: yfinance)...")
    try:
        # Note: Check if 'info' or similar exists in 'equity.fundamental' or 'equity.profile'
        # In v4, it is usually `obb.equity.profile`
        profile_data = obb.equity.profile(symbol=symbol, provider="yfinance")
        # profile_data is an OBBject
        results = profile_data.results
        print("Success!")
        if isinstance(results, list) and results:
            print(results[0])
        else:
            print(results)
            
    except Exception as e:
        print(f"FAILED to fetch profile: {e}")

if __name__ == "__main__":
    test_openbb_light()
