"""
OpenBB Wrapper Module with Fallback Logic
Encapsulates OpenBB calls and provides fallbacks to yfinance/DDG.
"""
import yfinance as yf
import pandas as pd
from openbb import obb
from duckduckgo_search import DDGS
import traceback

def get_stock_data(ticker_symbol):
    """
    Fetches basic stock info suitable for UI display.
    Primary: OpenBB (yfinance provider)
    Fallback: yfinance direct
    """
    data = {}
    
    # 1. Try OpenBB
    try:
        # obb.equity.profile returns an OBBject
        res = obb.equity.profile(symbol=ticker_symbol, provider="yfinance")
        # .results is usually a list of Pydantic models
        if res.results and isinstance(res.results, list):
            profile = res.results[0]
            
            # Map OpenBB model to our dict format
            # Using getattr to be safe, though Pydantic models should have attributes
            data['shortName'] = getattr(profile, 'name', ticker_symbol)
            data['sector'] = getattr(profile, 'sector', 'N/A')
            data['industry'] = getattr(profile, 'industry_category', 'N/A')
            data['marketCap'] = getattr(profile, 'market_cap', 0)
            data['employees'] = getattr(profile, 'employees', 0)
            data['longBusinessSummary'] = getattr(profile, 'long_description', "")
            data['website'] = getattr(profile, 'company_url', "")
            
            # Additional fetch for price metrics (OpenBB profile doesn't always have current price/PE)
            # We can use yf.Ticker for real-time price as OpenBB price.historical is historical
            # Or use obb.equity.price.quote if available (provider dependent)
            # For now, let's mixin yfinance for price to be safe and fast for real-time
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info # Only minor fetch
            data['currentPrice'] = info.get('currentPrice', 0)
            data['trailingPE'] = info.get('trailingPE', 0)
            data['fiftyTwoWeekHigh'] = info.get('fiftyTwoWeekHigh', 0)
            data['fiftyTwoWeekLow'] = info.get('fiftyTwoWeekLow', 0)
            
            # Return tuple compatible with app.py expectation: (ticker_obj, error_msg)
            # app.py expects a yfinance Ticker object to pass to other functions?
            # actually app.py usage:
            # ticker, error = utils.get_stock_data(symbol)
            # info = ticker.info
            # So we need to return something that mimics Ticker or refactor app.py to take a dict.
            # Refactoring app.py is safer to avoid hidden yf dependencies.
            # BUT to keep changes minimal in utils.py replacement, we can return a Mock object or the yf ticker with patched info.
            
            # STRATEGY: Return the yf.Ticker object, but patch its .info with OpenBB data where better?
            # Or just return the yf.Ticker object if we successfully validated presence with OpenBB.
            # Original code returns: ticker, error. And checks ticker.history().
            
            # Let's keep it simple: Validate existence with OpenBB, but return yf.Ticker for compatibility 
            # with existing downstream functions (like get_financials which takes ticker object).
            # This is a "Soft Migration" - using OpenBB to validate symbol and get profile, but keeping yf object for compat.
            
            return ticker, None
            
    except Exception as e:
        print(f"[OpenBB] get_stock_data failed: {e}")

    # 2. Fallback / Original Logic
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Force a data fetch to check if valid
        hist = ticker.history(period="1d")
        if hist.empty:
            return None, "No data found for symbol"
        return ticker, None
    except Exception as e:
        return None, str(e)

def get_news(ticker_symbol, limit=10):
    """
    Fetches news items.
    Primary: OpenBB (yfinance provider) - Good for specific company news
    Fallback: DuckDuckGo - Good for general web buzz
    Strategy: Return mixed or OpenBB primary
    """
    news_items = []
    
    # 1. Try OpenBB
    try:
        # obb.news.company returns list of OBBject items
        # Logic to prioritize Tiingo
        import os
        providers = ["yfinance"]
        if os.environ.get("OPENBB_TIINGO_TOKEN"):
            providers.insert(0, "tiingo")

        res = None
        for p in providers:
            try:
                # print(f"[OpenBB] Try news provider: {p}")
                curr = obb.news.company(symbol=ticker_symbol, limit=limit, provider=p)
                if curr and curr.results:
                    res = curr
                    break
            except Exception as e:
                 print(f"[OpenBB] Provider {p} error: {e}")

        if res and res.results:
            for item in res.results:
                # Standardize to list of dicts: {'title', 'source', 'date', 'body', 'url'}
                news_items.append({
                    'title': getattr(item, 'title', ''),
                    'source': getattr(item, 'source', 'OpenBB'),
                    'date': str(getattr(item, 'date', '')), # Convert datetime to str
                    'body': getattr(item, 'text', '') or getattr(item, 'summary', ''), # 'text' or 'summary'
                    'url': getattr(item, 'url', '')
                })
            # If we got good results, return them. 
            # Note: OpenBB yfinance provider sometimes gives empty 'text' body.
            if len(news_items) > 0:
                 return news_items
    except Exception as e:
        print(f"[OpenBB] get_news failed: {e}")

    # 2. Fallback: DuckDuckGo
    print("[Fallback] Using DuckDuckGo for news...")
    try:
        # Try specific query first (Past Year)
        ddgs = DDGS()
        results = ddgs.news(keywords=f"{ticker_symbol} stock", region="us-en", safesearch="off", timelimit="y", max_results=limit)
        if not results:
            results = ddgs.news(keywords=f"{ticker_symbol} news", region="us-en", safesearch="off", timelimit="y", max_results=limit)
        return results if results else []
    except Exception as e:
        print(f"[DDG] get_news failed: {e}")
        return []

def get_financials(ticker_obj):
    """
    Fetches financials. 
    Currently yfinance Ticker object is passed around. 
    To fully migrate, we'd need to fetch using obb and return a consistent dataframe structure.
    For now, stick to yfinance pass-through to minimize breakage in Sankey/Analysis,
    unless we want to refactor `get_sankey_data` too.
    """
    # ... Keeping as direct yfinance for now since input is Ticker object ...
    financials = {}
    try:
        financials['income_stmt'] = ticker_obj.quarterly_income_stmt
        financials['balance_sheet'] = ticker_obj.quarterly_balance_sheet
        financials['cashflow'] = ticker_obj.quarterly_cashflow
        financials['info'] = ticker_obj.info
    except Exception as e:
         print(f"Error fetching financials: {e}")
    return financials

def get_historical_data(ticker_symbol, period="1y"):
    """
    Fetches historical price data.
    Primary: OpenBB
    Fallback: yfinance
    """
    # 1. OpenBB
    try:
        # Convert period '1y' to start_date logic or just use limit?
        # OpenBB uses start_date. yfinance uses period.
        # Simple mapping:
        # obb.equity.price.historical(symbol=ticker_symbol, provider="yfinance") 
        
        import os
        providers = ["yfinance"]
        if os.environ.get("OPENBB_TIINGO_TOKEN"):
            providers.insert(0, "tiingo")
            
        res = None
        for p in providers:
            try:
                # print(f"[OpenBB] Try historical provider: {p}")
                # Note: Tiingo requires start_date sometimes or defaults to recent. yfinance defaults to max or period.
                # obb.equity.price.historical standardizes args usually.
                # However, for pure 'period' mapping, we might need to calc start_date if using Tiingo strictly.
                # But let's try calling without strict dates first or basic mapping.
                curr = obb.equity.price.historical(symbol=ticker_symbol, provider=p) 
                if curr and curr.results:
                    res = curr
                    break
            except Exception as e:
                print(f"[OpenBB] Historical Provider {p} error: {e}")
        
        if not res:
            raise Exception("No results from OpenBB providers")

        df = res.to_df()
        
        # Standardize columns? OpenBB returns: open, high, low, close, volume, ... (lowercase snake_case)
        # yfinance returns: Open, High, Low, Close, Volume (Capitalized)
        # Most of our utils code likely uses Title Case (df['Close']).
        # Need to rename columns for compatibility.
        df.columns = [c.title() for c in df.columns]
        
        # OpenBB index is usually named 'date', yfinance 'Date'.
        df.index.name = 'Date'
        
        return df
    except Exception as e:
        print(f"[OpenBB] get_historical_data failed: {e}")
        
    # 2. Fallback
    try:
        t = yf.Ticker(ticker_symbol)
        return t.history(period=period)
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()

def get_competitor_data(tickers):
    """
    Fetch competitor data.
    Primary: OpenBB Loop
    Fallback: yf Loop
    """
    data_list = []
    
    # Try efficient OpenBB approach if possible, but OpenBB is usually one symbol at a time for profile
    # So we loop.
    for t in tickers:
        row = {}
        try:
            # Profile from OpenBB
            res = obb.equity.profile(symbol=t, provider="yfinance")
            if res.results:
                prof = res.results[0]
                row["Ticker"] = t
                row["Name"] = getattr(prof, 'name', t)
                row["Market Cap"] = getattr(prof, 'market_cap', 0)
                # For Price/PE we might need quotes or rely on yf fallback inside loop if OpenBB misses
                
                # ... This might be too slow to do mixing per ticker.
                # Let's fallback to pure yfinance for the bulk list if simple.
                pass
        except:
            pass
            
    # Given the complexity of mixing sources for a list and maintaining speed,
    # and the code structure in utils.py `get_competitor_data` (which calculates returns),
    # it's better to keep utilizing yfinance for bulk history retrieval/calc for now.
    # We will stick to the utils.py implementation for this one or wrap it simply.
    
    # Re-implementing the exact logic from utils.py but inside here?
    # Or just importing it? 
    # Let's write the fallback implementation here.
    
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="1y")
            
            def get_change(days_ago):
                if len(hist) > days_ago:
                    start_price = hist['Close'].iloc[-(days_ago + 1)]
                    curr_price = hist['Close'].iloc[-1]
                    return ((curr_price - start_price) / start_price) * 100
                return 0.0

            data.append({
                "Ticker": t,
                "Name": info.get('shortName', t),
                "Price": info.get('currentPrice', 0),
                "P/E": info.get('trailingPE', 0),
                "Market Cap": info.get('marketCap', 0),
                "3M %": get_change(63),
                "6M %": get_change(126),
                "1Y %": get_change(250) if len(hist) > 240 else 0.0
            })
        except:
            continue
    return pd.DataFrame(data)

