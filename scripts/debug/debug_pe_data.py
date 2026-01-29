
import yfinance as yf
import pandas as pd

tickers = ["NVDA", "CAVA", "TSLA"]

for symbol in tickers:
    print(f"\n\n=== DEBUGGING {symbol} ===")
    try:
        t = yf.Ticker(symbol)
        ed = t.earnings_dates
        if ed is None or ed.empty:
            print("Earnings dates is EMPTY or None")
            continue
            
        print(f"Earnings Dates Shape: {ed.shape}")
        print("Columns:", ed.columns)
        print("First 5 rows:")
        print(ed.head())
        
        # Check Reported EPS
        if 'Reported EPS' in ed.columns:
            valid_eps = ed['Reported EPS'].dropna()
            print(f"Valid Reported EPS count: {len(valid_eps)}")
            print("Last 5 valid EPS:")
            print(valid_eps.sort_index().tail())
        else:
            print("'Reported EPS' column NOT FOUND")

    except Exception as e:
        print(f"Error: {e}")
