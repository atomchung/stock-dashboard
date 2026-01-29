from openbb import obb
import yfinance as yf
import json

print("\n--- DIAGNOSIS: NEWS (NVDA) ---")
try:
    # Try fetching news via OBB
    # Note: If openbb-news is not installed yet, this will fail or return None/Empty
    res = obb.news.company(symbol="NVDA", provider="yfinance", limit=3)
    print(f"OBB News Result Type: {type(res)}")
    if res and res.results:
        print(f"Count: {len(res.results)}")
        print("First Item Raw:")
        # Dump the first item's dict if possible
        try:
            print(res.results[0].model_dump())
        except:
            print(res.results[0])
    else:
        print("OBB returned NO results.")
except Exception as e:
    print(f"OBB News Error: {e}")

print("\n--- DIAGNOSIS: CALENDAR (NVDA) ---")
try:
    t = yf.Ticker("NVDA")
    cal = t.calendar
    print(f"Calendar Type: {type(cal)}")
    print("Content:")
    print(cal)
    
    # Test accessor logic from obb_utils.py
    if isinstance(cal, dict):
        print("Is Dict. Keys:", cal.keys())
        print("Earnings Date val:", cal.get("Earnings Date"))
    else:
        print("Is likely DataFrame.")
        if hasattr(cal, "index"):
            print("Index:", cal.index)
        if hasattr(cal, "columns"):
            print("Columns:", cal.columns)
            
except Exception as e:
    print(f"Calendar Error: {e}")
