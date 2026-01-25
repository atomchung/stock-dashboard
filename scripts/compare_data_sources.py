import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
"""
Data Source Comparison Demo
Compare yfinance/DuckDuckGo (current) vs OpenBB for a given ticker.

Usage:
    source .venv_openbb/bin/activate
    python compare_data_sources.py AAPL
"""

import argparse
import sys
from datetime import datetime

# ============ Current Approach: yfinance + DuckDuckGo ============
import yfinance as yf
from duckduckgo_search import DDGS

def get_data_yfinance(ticker_symbol):
    """Fetch stock data using yfinance (current approach)."""
    print("\n" + "="*60)
    print("📊 [Current] yfinance - Stock Data")
    print("="*60)
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        print(f"Name: {info.get('shortName', 'N/A')}")
        print(f"Sector: {info.get('sector', 'N/A')}")
        print(f"Industry: {info.get('industry', 'N/A')}")
        print(f"Market Cap: ${info.get('marketCap', 0):,.0f}")
        print(f"Current Price: ${info.get('currentPrice', 0):.2f}")
        print(f"52W High: ${info.get('fiftyTwoWeekHigh', 0):.2f}")
        print(f"52W Low: ${info.get('fiftyTwoWeekLow', 0):.2f}")
        print(f"PE Ratio: {info.get('trailingPE', 'N/A')}")
        
        # Recent Price History
        hist = ticker.history(period="5d")
        print("\nRecent Price History (5 days):")
        print(hist[['Close', 'Volume']].tail())
        
        return info
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def get_news_ddg(ticker_symbol):
    """Fetch news using DuckDuckGo (current approach)."""
    print("\n" + "="*60)
    print("📰 [Current] DuckDuckGo - News")
    print("="*60)
    
    try:
        results = DDGS().news(
            keywords=f"{ticker_symbol} stock",
            region="us-en",
            safesearch="off",
            timelimit="w",  # Past week
            max_results=5
        )
        
        if results:
            for i, item in enumerate(results, 1):
                print(f"\n{i}. {item.get('title', 'N/A')}")
                print(f"   Source: {item.get('source', 'N/A')}")
                print(f"   Date: {item.get('date', 'N/A')}")
        else:
            print("No news found.")
        
        return results
    except Exception as e:
        print(f"ERROR: {e}")
        return []

# ============ New Approach: OpenBB ============
from openbb import obb

def get_data_openbb(ticker_symbol):
    """Fetch stock data using OpenBB."""
    print("\n" + "="*60)
    print("📊 [OpenBB] equity.profile + equity.price.historical")
    print("="*60)
    
    try:
        # Profile
        profile = obb.equity.profile(symbol=ticker_symbol, provider="yfinance")
        p = profile.results
        if isinstance(p, list) and p:
            p = p[0]
        
        print(f"Name: {getattr(p, 'name', 'N/A')}")
        print(f"Sector: {getattr(p, 'sector', 'N/A')}")
        print(f"Industry: {getattr(p, 'industry_category', 'N/A')}")
        print(f"Market Cap: ${getattr(p, 'market_cap', 0):,.0f}")
        print(f"Employees: {getattr(p, 'employees', 'N/A')}")
        print(f"Dividend Yield: {getattr(p, 'dividend_yield', 'N/A')}%")
        print(f"Beta: {getattr(p, 'beta', 'N/A')}")
        
        # Price History
        price = obb.equity.price.historical(symbol=ticker_symbol, provider="yfinance", limit=5)
        df = price.to_df()
        print("\nRecent Price History (5 days):")
        print(df[['close', 'volume']].tail())
        
        return p
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def get_news_openbb(ticker_symbol):
    """Fetch news using OpenBB."""
    print("\n" + "="*60)
    print("📰 [OpenBB] news.company (yfinance provider)")
    print("="*60)
    
    try:
        news = obb.news.company(symbol=ticker_symbol, provider="yfinance", limit=5)
        results = news.results
        
        if results:
            for i, item in enumerate(results, 1):
                title = getattr(item, 'title', 'N/A')
                source = getattr(item, 'source', 'N/A')
                date = getattr(item, 'date', 'N/A')
                print(f"\n{i}. {title}")
                print(f"   Source: {source}")
                print(f"   Date: {date}")
        else:
            print("No news found.")
        
        return results
    except Exception as e:
        print(f"ERROR: {e}")
        return []

# ============ Main ============
def main():
    parser = argparse.ArgumentParser(description="Compare data sources for a stock ticker")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    print(f"\n{'#'*60}")
    print(f"# Comparing Data Sources for: {ticker}")
    print(f"# Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    # Current Approach
    get_data_yfinance(ticker)
    get_news_ddg(ticker)
    
    # OpenBB Approach
    get_data_openbb(ticker)
    get_news_openbb(ticker)
    
    print("\n" + "="*60)
    print("✅ Comparison Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
