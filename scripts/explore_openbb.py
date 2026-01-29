

try:
    from openbb import obb
    print("OpenBB imported from package")
except ImportError:
    print("OpenBB package missing")

import yfinance as yf
import pandas as pd

symbol = "NVDA"

print(f"\n--- Checking OpenBB Basic Profile for {symbol} ---")
try:
    # This was working in obb_utils.py
    res = obb.equity.profile(symbol=symbol, provider="yfinance")
    print("Profile fetch success")
except Exception as e:
    print(f"OpenBB Profile Error: {e}")
    # Print dir(obb) to see what IS available
    print(f"obb attributes: {dir(obb)}")
    if hasattr(obb, 'equity'):
        print(f"obb.equity attributes: {dir(obb.equity)}")

print(f"\n--- Checking yfinance Direct EPS for {symbol} ---")
try:
    ticker = yf.Ticker(symbol)
    
    print("\n1. Income Statement (Annual):")
    print(ticker.income_stmt.loc['Basic EPS'] if 'Basic EPS' in ticker.income_stmt.index else "No Basic EPS found")
    
    print("\n2. Income Statement (Quarterly):")
    # This is what we really want for the "Band"
    q_inc = ticker.quarterly_income_stmt
    if 'Basic EPS' in q_inc.index:
        print(q_inc.loc['Basic EPS'])
    else:
        print("No Quarterly Basic EPS found")

    print("\n3. Earnings History (if available):")
    # Sometimes earnings_history is available?
    # ticker.earnings_dates is useful for exact dates
    # print(ticker.earnings_dates.head()) 
    pass

except Exception as e:
    print(f"yfinance Error: {e}")
