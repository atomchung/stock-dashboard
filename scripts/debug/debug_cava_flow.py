
import sys
import os
sys.path.append(os.getcwd())
import utils
import pandas as pd
import time

def debug_flow():
    ticker_symbol = "CAVA"
    print(f"--- 1. Getting Stock Data for {ticker_symbol} ---")
    start = time.time()
    ticker, error = utils.get_stock_data(ticker_symbol)
    print(f"Done in {time.time() - start:.2f}s. Error: {error}")
    
    if error:
        return

    print("\n--- 2. Getting News ---")
    start = time.time()
    news = utils.get_news(ticker_symbol)
    print(f"Done in {time.time() - start:.2f}s. Items: {len(news)}")

    print("\n--- 3. Getting Financials ---")
    start = time.time()
    financials = utils.get_financials(ticker)
    inc = financials.get('income_stmt')
    print(f"Done in {time.time() - start:.2f}s. Income Stmt Empty? {inc.empty if inc is not None else 'True'}")

    print("\n--- 4. Getting Historical Data ---")
    start = time.time()
    hist = utils.get_historical_data(ticker)
    print(f"Done in {time.time() - start:.2f}s. Rows: {len(hist)}")

    print("\n--- 5. Getting Sankey Data ---")
    start = time.time()
    # Mock segments json
    segments_json = "[]"
    sankey = utils.get_sankey_data(ticker_symbol, financials, segments_json, agent=None)
    print(f"Done in {time.time() - start:.2f}s. Sankey Data: {sankey is not None}")

if __name__ == "__main__":
    try:
        debug_flow()
    except KeyboardInterrupt:
        print("\nInterrupted!")
    except Exception as e:
        print(f"\nCRASHED: {e}")
