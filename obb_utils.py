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
                # Helper to safely get attribute or dict key
                def get_val(obj, key, default=''):
                    if isinstance(obj, dict):
                        return obj.get(key, default)
                    return getattr(obj, key, default)

                # Standardize to list of dicts: {'title', 'source', 'date', 'body', 'url'}
                # Yfinance provider often puts content in 'summary' or 'text'
                body = get_val(item, 'body') or get_val(item, 'text') or get_val(item, 'summary') or ''
                
                news_items.append({
                    'title': get_val(item, 'title', ''),
                    'source': get_val(item, 'source', 'OpenBB'),
                    'date': str(get_val(item, 'date', '')), # Convert datetime to str
                    'body': body, 
                    'url': get_val(item, 'url', '')
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

def get_calendar_events(ticker_symbol):
    """
    Fetches major calendar events (Earnings, Dividends).
    
    Data Sources (in order):
    1. Daily cache (to minimize API calls)
    2. FMP Earnings Calendar API (most reliable)
    3. yfinance calendar (fallback)
    """
    import earnings_cache_manager
    import requests
    import os
    from datetime import datetime, timedelta
    
    # 1. Check cache first
    cached = earnings_cache_manager.get_cached_earnings(ticker_symbol)
    if cached is not None:
        return cached
    
    dates = {}
    
    # 2. Try FMP API (new /stable endpoint)
    fmp_key = os.environ.get("FMP_API_KEY")
    if fmp_key:
        try:
            # FMP /stable/earnings - returns all earnings history/future for a symbol
            url = f"https://financialmodelingprep.com/stable/earnings?symbol={ticker_symbol.upper()}&apikey={fmp_key}"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check for API error message
                if isinstance(data, dict) and 'Error Message' in data:
                    print(f"[FMP] API Error: {data['Error Message']}")
                elif isinstance(data, list) and len(data) > 0:
                    # Find next future earnings (epsActual is null for future dates)
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    
                    for item in data:
                        item_date = item.get('date', '')
                        eps_actual = item.get('epsActual')
                        
                        # Future earnings: date >= today AND epsActual is null
                        if item_date >= today_str and eps_actual is None:
                            dates['next_earnings'] = item_date
                            # Capture EPS estimate if available
                            eps_est = item.get('epsEstimated')
                            if eps_est:
                                dates['eps_estimated'] = eps_est
                            # Capture revenue estimate
                            rev_est = item.get('revenueEstimated')
                            if rev_est:
                                dates['revenue_estimated'] = rev_est
                            dates['source'] = 'FMP'
                            print(f"[FMP] Found next earnings date for {ticker_symbol}: {item_date}")
                            break
                    
                    # Cache the result
                    earnings_cache_manager.save_earnings(ticker_symbol, dates)
                    
                    if dates.get('next_earnings'):
                        return dates
                        
        except Exception as e:
            print(f"[FMP] Error fetching earnings: {e}")
    
    # 3. Fallback to yfinance for dividend info and as backup
    try:
        ticker = yf.Ticker(ticker_symbol)
        calendar = ticker.calendar
        
        if calendar is not None and not calendar.empty:
            # Handle both Dict and DataFrame formats from yfinance
            if isinstance(calendar, dict):
                earnings = calendar.get('Earnings Date')
                div = calendar.get('Dividend Date')
                ex_div = calendar.get('Ex-Dividend Date')
            else:
                try:
                    earnings = calendar.loc['Earnings Date'].values if 'Earnings Date' in calendar.index else None
                    div = calendar.loc['Dividend Date'].values if 'Dividend Date' in calendar.index else None
                    ex_div = calendar.loc['Ex-Dividend Date'].values if 'Ex-Dividend Date' in calendar.index else None
                except:
                    earnings = None
                    div = None
                    ex_div = None

            # Only use yfinance earnings if FMP didn't find any
            if not dates.get('next_earnings') and earnings is not None:
                val = earnings[0] if (isinstance(earnings, list) or hasattr(earnings, '__iter__')) and len(earnings) > 0 else earnings
                if val: 
                    dates['next_earnings'] = str(val)
                    dates['source'] = 'yfinance'

            if div is not None:
                val = div[0] if (isinstance(div, list) or hasattr(div, '__iter__')) and len(div) > 0 else div
                if val: dates['dividend_date'] = str(val)

            if ex_div is not None:
                val = ex_div[0] if (isinstance(ex_div, list) or hasattr(ex_div, '__iter__')) and len(ex_div) > 0 else ex_div
                if val: dates['ex_dividend'] = str(val)
                
    except Exception as e:
        print(f"[yfinance] Error fetching calendar: {e}")
    
    # Cache final result
    earnings_cache_manager.save_earnings(ticker_symbol, dates)
    
    return dates

def get_pe_band_data(ticker_symbol):
    """
    Calculates PE Band data for the last 2 years.
    Returns a DataFrame with columns: ['Close', 'PE_15x', 'PE_20x', 'PE_25x']
    Uses yfinance earnings_dates to reconstruct historical TTM EPS.
    """
    try:
        t = yf.Ticker(ticker_symbol)
        
        # 1. Get Earnings History
        # earnings_dates 'Reported EPS' is what we need.
        ed = t.earnings_dates
        if ed is None or ed.empty:
            return pd.DataFrame()

        # Clean and Sort
        # Filter for actual reported EPS (remove future estimates/NaNs)
        ed = ed.dropna(subset=['Reported EPS']).sort_index()
        
        # 2. Calculate TTM EPS
        # TTM EPS at any point is the sum of the last 4 reported EPS.
        # We calculate rolling sum.
        ed['TTM_EPS'] = ed['Reported EPS'].rolling(window=4).sum()
        
        # 3. Fetch Price History (2y)
        hist = t.history(period="2y")
        if hist.empty:
            return pd.DataFrame()
            
        merged_df = pd.DataFrame(index=hist.index)
        merged_df['Close'] = hist['Close']
        
        # 4. Merge EPS onto Price Dates
        # We want the known TTM EPS for each day.
        # Join earnings dates to price dates.
        # Since earnings dates are sparse, we use reindex + ffill.
        # Note: Earnings Date is when the market knows the new EPS.
        
        # Create a series indexed by date for TTM EPS
        eps_series = ed['TTM_EPS']
        
        # Reindex EPS series to match price index (union of indices first to handle gaps?)
        # Better: use merge_asof or reindex with method='ffill'
        # But we need to be careful about timezone. yfinance price index is usually tz-aware.
        # earnings_dates index is also tz-aware usually.
        
        # Ensure timezone compatibility
        if eps_series.index.tz is None and hist.index.tz is not None:
             eps_series.index = eps_series.index.tz_localize(hist.index.tz)
        elif eps_series.index.tz is not None and hist.index.tz is None:
             eps_series.index = eps_series.index.tz_localize(None)
        elif eps_series.index.tz != hist.index.tz:
             eps_series.index = eps_series.index.tz_convert(hist.index.tz)
             
        # Reindex and forward fill
        # We only want dates present in price history
        aligned_eps = eps_series.reindex(hist.index, method='ffill')
        
        # 5. Calculate Bands
        merged_df['PE_15x'] = aligned_eps * 15
        merged_df['PE_20x'] = aligned_eps * 20
        merged_df['PE_25x'] = aligned_eps * 25
        
        return merged_df
        
    except Exception as e:
        print(f"Error calculating PE Band data: {e}")
        return pd.DataFrame()


