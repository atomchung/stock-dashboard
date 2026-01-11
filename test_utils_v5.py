import utils
import pandas as pd

def test_fetch_v5():
    print("Testing Financial Analysis Search...")
    res = utils.search_financial_analysis("TSLA") 
    if res:
        print(f"SUCCESS: Found context results. Count: {len(res)}")
    else:
        print("WARNING: No search results found for financial analysis.")

    print("Testing Deep Financials Extraction...")
    ticker, _ = utils.get_stock_data("TSLA")
    fin = utils.get_financials(ticker)
    
    inc = fin.get('income_stmt')
    if not inc.empty:
        # Check EPS and Gross Profit existence in info or table
        info = fin.get('info', {})
        if 'trailingEps' in info:
            print(f"SUCCESS: EPS found: {info['trailingEps']}")
        else:
             print("WARNING: EPS not found in info.")

        if 'grossProfits' in info or 'Gross Profit' in inc.index:
             print("SUCCESS: Gross Profit found.")
    else:
        print("FAILED: No Income Stmt.")

if __name__ == "__main__":
    test_fetch_v5()
