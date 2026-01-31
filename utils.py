import yfinance as yf
import pandas as pd
import ta
from duckduckgo_search import DDGS # Restored for Deep Search
import obb_utils
import json

import os
import requests


def get_stock_data(ticker_symbol):
    """
    Fetches the yfinance Ticker object and basic info using OpenBB/Fallback.
    """
    return obb_utils.get_stock_data(ticker_symbol)

def get_earnings_dates(ticker_symbol):
    """
    Returns confirmed future earnings date using obb_utils (Centralized).
    """
    return obb_utils.get_calendar_events(ticker_symbol)

def get_news(ticker_symbol):
    """
    Returns a list of news items using OpenBB with DDG fallback.
    """
    return obb_utils.get_news(ticker_symbol)



def format_large_number(num):
    """
    Formats a large number into readable string with suffix (T, B, M, K).
    """
    if not num or isinstance(num, str):
        return str(num)
    
    try:
        num = float(num)
        if num >= 1e12:
            return f"${num/1e12:.2f}T"
        elif num >= 1e9:
            return f"${num/1e9:.2f}B"
        elif num >= 1e6:
            return f"${num/1e6:.2f}M"
        elif num >= 1e3:
            return f"${num/1e3:.2f}K"
        else:
            return f"${num:.2f}"
    except:
        return str(num)

def search_earnings_context(ticker_symbol):
    """
    Searches for earnings call takeaways and financial analysis.
    Enhanced with multi-dimensional search for small-cap stock coverage.
    """
    try:
        # Get company name for better search coverage
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            info = ticker_obj.info
            company_name = info.get('shortName', ticker_symbol)
            sector = info.get('sector', '')
        except:
            company_name = ticker_symbol
            sector = ''
        
        results = []
        seen_urls = set()
        
        # Multi-dimensional search strategy
        search_queries = [
            # Tier 1: Company name + earnings (most specific)
            f'"{company_name}" earnings report revenue growth',
            f'"{company_name}" quarterly results analysis',
            
            # Tier 2: Ticker + investment thesis
            f'{ticker_symbol} stock investment thesis bull case',
            f'{ticker_symbol} stock risks challenges bear case',
            
            # Tier 3: Company + financial metrics
            f'"{company_name}" gross margin operating income',
        ]
        
        for query in search_queries:
            try:
                # Use web search for broader coverage (not just news)
                web_results = list(DDGS().text(
                    keywords=query, 
                    region="us-en", 
                    safesearch="off",
                    max_results=3
                ))
                
                for r in web_results:
                    url = r.get('href', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        # Extract domain for quality scoring
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else ''
                        results.append({
                            'title': r.get('title', ''),
                            'body': r.get('body', ''),
                            'url': url,
                            'source': domain,
                        })
            except Exception as e:
                print(f"Search query failed: {query} - {e}")
                continue
        
        # Also run news search for recent coverage
        try:
            news_results = DDGS().news(
                keywords=f"{ticker_symbol} OR \"{company_name}\" earnings",
                region="us-en", 
                safesearch="off", 
                timelimit="6m",  # Last 6 months for fresher data
                max_results=5
            )
            for item in news_results:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(item)
        except:
            pass
        
        # Quality-based sorting: prioritize authoritative sources
        quality_sources = ['sec.gov', 'seekingalpha', 'bloomberg', 'reuters', 'wsj', 'yahoo', 'nasdaq']
        
        def quality_score(item):
            source = str(item.get('source', item.get('url', ''))).lower()
            for i, qs in enumerate(quality_sources):
                if qs in source:
                    return i
            return len(quality_sources)
        
        results.sort(key=quality_score)
        
        print(f"DEBUG: search_earnings_context found {len(results)} results for {ticker_symbol}")
        return results[:12]  # Return top 12 quality results
        
    except Exception as e:
        print(f"Error searching earnings context: {e}")
        return []





def search_key_events(ticker_symbol):
    """
    Searches for major events using a Hybrid approach (Web for Dates + News for Events).
    """
    try:
        results = []
        
        # 1. Broad Web Search for Specific Dates (Calendars, Earnings)
        # Targeted for sites like Nasdaq, MarketBeat, Yahoo Finance
        query_date = f"{ticker_symbol} next earnings date"
        web_results = list(DDGS().text(keywords=query_date, region="us-en", safesearch="off", max_results=4))
        print(f"DEBUG: '{query_date}' -> {len(web_results)} results")
        if web_results:
             results.extend(web_results)
        
        # 2. News Search for Recent/Upcoming Developments
        query_news = f"{ticker_symbol} corporate news product launch FDA approval"
        news_results = DDGS().news(keywords=query_news, region="us-en", safesearch="off", max_results=3)
        if news_results:
             results.extend(news_results)
             
        return results
    except Exception as e:
        print(f"Error searching key events: {e}")
        return []



def search_financial_analysis(ticker_symbol):
    """
    Searches for specific analysis on financial results (Why revenue/margins changed).
    """
    try:
        query = f"{ticker_symbol} financial results analysis revenue profit drivers"
        results = DDGS().news(keywords=query, region="us-en", safesearch="off", timelimit="y", max_results=5)
        return results
    except Exception as e:
        print(f"Error searching financial analysis: {e}")
        return []



def search_revenue_segments(ticker_symbol):
    """
    Searches for revenue breakdown by segment.
    """
    try:
        query = f"{ticker_symbol} revenue breakdown by segment earnings report"
        results = DDGS().news(keywords=query, region="us-en", safesearch="off", timelimit="y", max_results=5)
        return results
    except Exception as e:
        print(f"Error searching revenue segments: {e}")
        return []



def get_competitor_data(tickers):
    """
    Fetches basic metrics and 3M/6M/12M performance for a list of tickers.
    """
    return obb_utils.get_competitor_data(tickers)

def get_competitor_history(tickers):
    """
    Fetches 1y historical closing data for a list of tickers, normalized to % return.
    """
    if not tickers:
        return pd.DataFrame()
        
    try:
        data = yf.download(tickers, period="1y")['Close']
        # If single ticker result, it might be a Series, ensure DataFrame
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
            
        # Drop NaN columns (failed downloads)
        data = data.dropna(axis=1, how='all')
        
        # Normalize to percentage change
        if not data.empty:
            return (data / data.iloc[0] - 1) * 100
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching competitor history: {e}")
        return pd.DataFrame()

def get_sankey_data(ticker_symbol, financials, segments_json, agent=None):
    """
    Prepares node/link data for an Income Statement Sankey Diagram.
    
    Uses a 3-tier approach:
    1. Check cache for previously inferred structure
    2. If cache miss and agent provided, use AI to infer structure
    3. Fallback to simplified fixed structure
    """
    import sankey_cache_manager
    
    try:
        inc = financials.get('income_stmt', pd.DataFrame())
        if inc.empty:
            return None
        
        # Get most recent quarter data
        col = inc.columns[0]
        recent = inc[col]
        recent_dict = recent.to_dict()
        
        # Format date to YYQx (e.g. 2024-09-30 -> 24Q3)
        try:
            date_obj = pd.to_datetime(col)
            quarter = (date_obj.month - 1) // 3 + 1
            period_label = f"{date_obj.year % 100}Q{quarter}"
        except:
            period_label = str(col).split(' ')[0]

        # === Tier 1: Check Cache ===
        cached_structure = sankey_cache_manager.get_cached_structure(ticker_symbol)
        
        # === Tier 2: AI Inference (if no cache and agent available) ===
        if cached_structure is None and agent is not None:
            print(f"Cache miss for {ticker_symbol}, using AI to infer structure...")
            inferred = agent.infer_sankey_structure(recent_dict)
            if inferred:
                sankey_cache_manager.save_structure(ticker_symbol, inferred)
                cached_structure = inferred
        
        # === Tier 3: Use cached/inferred structure OR fallback ===
        if cached_structure:
            # === DYNAMIC ADJUSTMENT ===
            structure_to_use = _refine_structure_for_negatives(ticker_symbol, recent_dict, cached_structure)
            
            return _build_sankey_from_structure(
                ticker_symbol, recent_dict, structure_to_use, period_label, segments_json
            )
        else:
            # Fallback to simplified fixed structure
            return _build_sankey_fallback(ticker_symbol, recent, period_label, segments_json)
    
    except Exception as e:
        print(f"Sankey Error: {e}")
        return None


def _refine_structure_for_negatives(ticker, data, structure):
    """
    Dynamically adjusts the Sankey structure if specific financial inconsistencies are detected.
    Scenario: 'Other Income Expense' is negative (Loss), but flows OUT of 'Pretax Income'.
    Fix: 
      1. Rename current 'Pretax Income' node to 'Intermediate Sum' (e.g. Operating Results & Interest).
      2. Insert a new 'Pretax Income' node downstream.
      3. Reroute 'Tax' and 'Net Income' to flow from the new 'Pretax Income' node.
    """
    import copy
    refined = copy.deepcopy(structure)
    
    other_val = data.get('Other Income Expense', 0)
    
    # Only apply if Other Income is Negative (Expense)
    if other_val >= 0:
        return refined
        
    links = refined.get('links', [])
    nodes = refined.get('nodes', [])
    
    # Check if we have the problematic link: Pretax Income -> Other Income Expense
    problem_link = next((l for l in links if l.get('source') == 'Pretax Income' and 
                         (l.get('target') == 'Other Income Expense' or l.get('field') == 'Other Income Expense')), None)
    
    if problem_link:
        print(f"[{ticker}] Detected Negative Other Income flowing from Pretax Income. Adjusting topology...")
        
        # 1. Rename existing 'Pretax Income' node to something more accurate
        #    This node currently holds (Op Income + Interest), which effectively includes the money used for Other Expense
        pretax_node = next((n for n in nodes if n.get('name') == 'Pretax Income'), None)
        if pretax_node:
            pretax_node['name'] = 'Operating Results & Interest'
            
        # 2. Update the problematic link (Other Expense) to source from this renamed node
        #    (Since we just renamed the node in the node list, we update the link source name to match)
        problem_link['source'] = 'Operating Results & Interest'
        
        # 3. Create a NEW 'Pretax Income' node
        #    Layer should be same as 'Operating Results & Interest' (2) or slightly shifted? 
        #    Let's keep it at layer 2 to align with others, or pushing to 2.5 (visually handled by plotly usually)
        new_pretax = {
            "name": "Pretax Income",
            "layer": 2
        }
        nodes.append(new_pretax)
        
        # 4. Create a link from 'Operating Results & Interest' -> 'Pretax Income'
        #    The value implies passing the remaining profit.
        #    We don't need to specify value here, _build_sankey... calculates it.
        #    But we need a field mapping? 
        #    Actually, in _build_sankey, value is fetched from data[field]. 
        #    The dataframe has 'Pretax Income' = 20M. 
        #    So we map this link to field 'Pretax Income'.
        main_flow_link = {
            "source": "Operating Results & Interest",
            "target": "Pretax Income",
            "field": "Pretax Income"
        }
        links.append(main_flow_link)
        
        # 5. Retarget Tax and Net Income to source from the NEW 'Pretax Income'
        for link in links:
            if link.get('source') == 'Pretax Income' and link != problem_link:
                # This catches Tax and Net Income (old source name was Pretax Income)
                link['source'] = 'Pretax Income'
                
                # However, since we defined the new node with name 'Pretax Income', 
                # and the old node object was renamed to 'Operating Results...', 
                # any link referencing 'Pretax Income' as source is essentially broken 
                # unless we align the strings.
                
                # Wait, the 'links' list just uses string names.
                # In Step 1 we changed the NODE's name property. 
                # We did NOT change the strings in the LINK objects (except problem_link).
                # So currently, links still say source="Pretax Income".
                # The NEW node is named "Pretax Income".
                # So logically, these links typically AUTO-CONNECT to the new node!
                # EXCEPT: We want problem_link to connect to 'Operating Results'.
                
                # So:
                # - Problem Link source set to 'Operating Results & Interest' (DONE in step 2)
                # - New Main Flow Link source set to 'Operating Results & Interest' (DONE in step 4)
                # - Old, "good" links (Tax, Net Income) source is 'Pretax Income'.
                #   They will now attach to the NEW 'Pretax Income' node we added.
                pass

    return refined


def _build_sankey_from_structure(ticker_symbol, recent_dict, structure, period_label, segments_json):
    """
    Builds Sankey data from AI-inferred structure.
    """
    # Colors
    COLORS = {
        0: "#2E86C1",  # Blue (Revenue)
        1: "#28B463",  # Green (Profit) / Red for costs handled separately
        2: "#F39C12",  # Orange (OpEx)
        3: "#1E8449",  # Dark Green (Net Income)
    }
    COLOR_COST = "#E74C3C"  # Red for costs
    
    labels = []
    node_colors = []
    node_x = []
    node_y = []
    
    source = []
    target = []
    value = []
    link_colors = []
    custom_data = []
    
    # Build nodes from structure
    field_mapping = structure.get('field_mapping', {})
    nodes = structure.get('nodes', [])
    links = structure.get('links', [])
    
    # Create node index map
    node_index = {}
    
    # Sort nodes by layer for consistent positioning
    sorted_nodes = sorted(nodes, key=lambda n: (n.get('layer', 0), n.get('name', '')))
    
    for i, node in enumerate(sorted_nodes):
        name = node.get('name', f'Node{i}')
        layer = node.get('layer', 0)
        
        labels.append(name)
        node_index[name] = i
        
        # Determine color based on layer and name
        if 'cost' in name.lower() or 'expense' in name.lower() or 'tax' in name.lower():
            node_colors.append(COLOR_COST)
        else:
            node_colors.append(COLORS.get(layer, "#95A5A6"))
        
        # Calculate x position based on layer (0-1 range)
        max_layer = max(n.get('layer', 0) for n in nodes) or 1
        node_x.append(layer / max_layer * 0.8 + 0.1)
        
        # Y position will be auto-calculated by Plotly
        node_y.append(0.5)
    
    # Build links from structure
    for link in links:
        src_name = link.get('source', '')
        tgt_name = link.get('target', '')
        field_name = link.get('field', tgt_name)
        
        if src_name not in node_index or tgt_name not in node_index:
            continue
        
        # Get value from recent data using field mapping
        actual_field = field_mapping.get(tgt_name, field_name)
        val = abs(float(recent_dict.get(actual_field, 0) or 0))
        
        if val <= 0:
            continue
        
        source.append(node_index[src_name])
        target.append(node_index[tgt_name])
        value.append(val)
        
        # Determine link color based on target
        if 'cost' in tgt_name.lower() or 'expense' in tgt_name.lower() or 'tax' in tgt_name.lower():
            link_colors.append("rgba(231, 76, 60, 0.4)")
        elif 'profit' in tgt_name.lower() or 'income' in tgt_name.lower():
            link_colors.append("rgba(40, 180, 99, 0.4)")
        else:
            link_colors.append("rgba(180, 180, 180, 0.4)")
        
        custom_data.append(format_large_number(val))
    
    if not value:
        return None
    
    return {
        "period": period_label,
        "label": labels,
        "color": node_colors,
        "source": source,
        "target": target,
        "value": value,
        "link_color": link_colors,
        "custom_data": custom_data
    }


def _build_sankey_fallback(ticker_symbol, recent, period_label, segments_json):
    """
    Fallback: Simplified fixed structure for when AI is unavailable.
    Only shows Revenue -> Gross Profit/COGS -> Net Income.
    """
    # Colors
    COLOR_REV = "#2E86C1"
    COLOR_COST = "#E74C3C"
    COLOR_GP = "#28B463"
    COLOR_NET = "#1E8449"
    
    labels = []
    node_colors = []
    source = []
    target = []
    value = []
    link_colors = []
    custom_data = []
    
    def get_idx(name, color):
        if name not in labels:
            labels.append(name)
            node_colors.append(color)
        return labels.index(name)
    
    def add_link(src_name, src_color, tgt_name, tgt_color, val, link_color=None):
        if val <= 0:
            return
        s = get_idx(src_name, src_color)
        t = get_idx(tgt_name, tgt_color)
        source.append(s)
        target.append(t)
        value.append(val)
        link_colors.append(link_color if link_color else "rgba(180, 180, 180, 0.5)")
        custom_data.append(format_large_number(val))
    
    # Extract basic values
    total_rev = abs(recent.get('Total Revenue', 0) or 0)
    cogs = abs(recent.get('Cost Of Revenue', 0) or 0)
    gross_profit = abs(recent.get('Gross Profit', 0) or 0)
    net_income = abs(recent.get('Net Income', 0) or 0)
    
    if total_rev <= 0:
        return None
    
    # Build simplified structure
    add_link("Total Revenue", COLOR_REV, "Cost of Revenue", COLOR_COST, cogs, "rgba(231, 76, 60, 0.3)")
    add_link("Total Revenue", COLOR_REV, "Gross Profit", COLOR_GP, gross_profit, "rgba(40, 180, 99, 0.3)")
    
    if gross_profit > 0 and net_income > 0:
        add_link("Gross Profit", COLOR_GP, "Net Income", COLOR_NET, net_income, "rgba(30, 132, 73, 0.5)")
    
    if not value:
        return None
    
    return {
        "period": period_label,
        "label": labels,
        "color": node_colors,
        "source": source,
        "target": target,
        "value": value,
        "link_color": link_colors,
        "custom_data": custom_data
    }


def get_financials(ticker):
    """
    Returns specific financial dataframes (Quarterly).
    """
    financials = {}
    try:
        # Fetch quarterly financials for better trend analysis
        financials['income_stmt'] = ticker.quarterly_income_stmt
        financials['balance_sheet'] = ticker.quarterly_balance_sheet
        financials['cashflow'] = ticker.quarterly_cashflow
        financials['info'] = ticker.info
    except Exception as e:
        print(f"Error fetching financials: {e}")
    return financials

def get_historical_data(ticker, period="1y"):
    """
    Fetches historical price data using OpenBB (via obb_utils).
    """
    # Extract symbol if ticker is a yfinance Ticker object
    symbol = ticker.ticker if hasattr(ticker, 'ticker') else str(ticker)
    return obb_utils.get_historical_data(symbol, period)



def calculate_momentum(df):
    """
    Calculates RSI and Moving Averages using the 'ta' library.
    """
    if df.empty:
        return df
    
    # Simple Moving Averages
    df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    return df

def analyze_investment_signals(info, df):
    """
    Analyzes data to return list of signal strings.
    """
    signals = []
    
    if df.empty:
        return signals

    current_price = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1]
    
    # RSI Signals
    if rsi > 70:
        signals.append("⚠️ **RSI Overbought**: The stock might be overvalued in the short term.")
    elif rsi < 30:
        signals.append("🟢 **RSI Oversold**: The stock might be undervalued in the short term.")
    else:
        signals.append(f"ℹ️ **RSI Neutral**: Current RSI is {rsi:.2f}.")

    # Trend Signals
    if current_price > sma_50:
        signals.append("📈 **Bullish Trend**: Price is above the 50-day SMA.")
    else:
        signals.append("📉 **Bearish Trend**: Price is below the 50-day SMA.")

    return signals

def get_polymarket_data(ticker_symbol, company_name=None, extra_keywords=None):
    """
    Fetches top betting markets from Polymarket related to the ticker.
    Returns Top 5 by volume.
    
    Strictly filters results to contain Ticker, Company Name, or Extra Keywords.
    """
    try:
        seen_slugs = set()
        all_markets = []

        # Prepare Filter List (Case-Insensitive)
        filter_terms = {ticker_symbol.lower()}
        if company_name:
            # Add "Apple" from "Apple Inc."
            simple = company_name.split()[0].lower()
            filter_terms.add(simple)

        if extra_keywords:
            for k in extra_keywords:
                filter_terms.add(k.lower())

        def fetch_and_parse(query_term):
            url = "https://gamma-api.polymarket.com/public-search"
            params = {
                "q": query_term,
                "limit": 20,
                "type": "event",
                "closed": "false"
            }
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    # /public-search returns {'events': [...]}
                    if isinstance(data, dict):
                        return data.get('events', [])
                    elif isinstance(data, list):
                        return data
            except:
                pass
            return []

        # 1. Search by Ticker
        events_ticker = fetch_and_parse(ticker_symbol)
        
        # 2. Search by simple Company Name
        events_name = []
        if company_name:
            simple_name = company_name.split()[0]
            if simple_name.lower() != ticker_symbol.lower():
                events_name = fetch_and_parse(simple_name)

        # Combine & Strict Filter
        for event in events_ticker + events_name:
            slug = event.get('slug')
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            
            markets = event.get('markets', [])
            if not markets: continue
            mk = markets[0]
            
            title = event.get('title', mk.get('question'))
            
            # --- STRICT FILTERING ---
            # Title must contain at least one filter term
            title_lower = title.lower()
            if not any(term in title_lower for term in filter_terms):
                continue
            
            # Skip Closed/Archived Events or Markets
            if event.get('closed') or mk.get('closed') or event.get('archived'):
                continue
            # ------------------------

            volume = float(mk.get('volume', 0))
            
            # Extract Odds
            try:
                outcomes = json.loads(mk.get('outcomes', '[]'))
                prices = json.loads(mk.get('outcomePrices', '[]'))
                odds_str = []
                for out, price in zip(outcomes, prices):
                    p = float(price) * 100
                    odds_str.append(f"{out}: {p:.1f}%")
                odds_display = ", ".join(odds_str)
            except:
                odds_display = "Odds unavailable"
            
            all_markets.append({
                "title": title,
                "volume": volume,
                "odds": odds_display,
                "url": f"https://polymarket.com/event/{slug}"
            })
            
        # Client-side Sort
        all_markets.sort(key=lambda x: x['volume'], reverse=True)
        
        return all_markets[:5]
        
    except Exception as e:
        print(f"Error fetching Polymarket data: {e}")
        return []

def get_pe_band_data(ticker_symbol):
    """
    Calculates PE Bands (15x, 20x, 25x) based on Trailing EPS.
    Returns a DataFrame with Close Price and PE Band lines.
    Delegates to obb_utils implementation.
    """
    return obb_utils.get_pe_band_data(ticker_symbol)
