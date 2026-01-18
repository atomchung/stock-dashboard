import yfinance as yf
import pandas as pd
import ta
from duckduckgo_search import DDGS
import json

import google.generativeai as genai
import os
import requests

def get_stock_data(ticker_symbol):
    """
    Fetches the yfinance Ticker object and basic info.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Force a data fetch to check if valid
        _ = ticker.history(period="1d")
        if _.empty:
            return None, "No data found for symbol"
        return ticker, None
    except Exception as e:
        return None, str(e)

def get_news(ticker_symbol):
    """
    Returns a list of news items using DuckDuckGo.
    """
    try:
        # Try specific query first (Past Year)
        results = DDGS().news(keywords=f"{ticker_symbol} stock", region="us-en", safesearch="off", timelimit="y", max_results=10)
        # Fallback
        if not results:
            results = DDGS().news(keywords=f"{ticker_symbol} news", region="us-en", safesearch="off", timelimit="y", max_results=10)
        return results
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def summarize_news_with_ai(news_items, api_key):
    """
    Summarizes news using Gemini API.
    """
    if not api_key:
        return "Please provide a gemini API Key to see the summary."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')

        
        # Prepare content
        news_text = ""
        for i, item in enumerate(news_items[:7]): # Limit to 7 items
            news_text += f"{i+1}. {item.get('title')} ({item.get('source')}) - {item.get('body')}\n"
            
        prompt = f"""
        You are a financial analyst. Based on the following recent news titles and snippets, provide a concise summary of what is driving the stock's sentiment.
        
        Then, list the top 3 most important articles from the provided list. For each, strictly format it as:
        - **[Title]**: Why it's worth reading.
        
        **Formatting Rules (CRITICAL)**:
        - **NO LaTeX**: Do NOT use `$` signs to wrap sentences (e.g. `$Text$`). This causes spaces to disappear.
        - **Currency**: Write "$27.5 billion" or "27.5 billion USD". NEVER close the standard with another `$`.
        - **Markdown Only**: Use `**bold**` for emphasis. Do not use random `**` in sentences.

        **Entity Verification**:
        - Focus ONLY on news directly related to the specific company. 
        - If an article discusses a competitor (e.g. Nvidia) but only mentions this stock in passing, IGNORE it or explicitly state "In contrast to Nvidia...".
        - Do not halluncinate a connection if the article is purely about another stock.

        News Items:
        {news_text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error gathering AI summary: {e}. (Ensure API Key is valid and supports 'gemini-2.0-flash-exp')"

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

def get_sankey_data(ticker_symbol, financials, segments_json):
    """
    Prepares node/link data for an Income Statement Sankey Diagram.
    Style: App Economy (Blue Revenue, Green Profit, Red Costs).
    """
    try:
        inc = financials.get('income_stmt', pd.DataFrame())
        if inc.empty:
            return None
        
        # Get most recent quarter
        col = inc.columns[0]
        recent = inc[col]

        # Extract Core Values (Absolute positives)
        total_rev = abs(recent.get('Total Revenue', 0))
        cogs = abs(recent.get('Cost Of Revenue', 0))
        gross_profit = abs(recent.get('Gross Profit', 0))
        
        # OpEx Breakdown
        op_expense = abs(recent.get('Operating Expense', 0)) 
        rd = abs(recent.get('Research And Development', 0))
         # Fallback if specific lines missing
        if rd == 0:
             rd = 0
             
        sga = abs(recent.get('Selling General And Administration', 0))
        
        op_income = abs(recent.get('Operating Income', 0))
        
        tax = abs(recent.get('Tax Provision', 0))
        net_income = abs(recent.get('Net Income', 0))
        
        # Colors
        COLOR_REV = "#2E86C1" # Blue
        COLOR_COST = "#E74C3C" # Red
        COLOR_GP = "#28B463" # Green
        COLOR_OPEX = "#F39C12" # Orange
        COLOR_NET = "#1E8449" # Dark Green
        COLOR_GREY = "#95A5A6"
        
        # --- Nodes ---
        labels = []
        node_colors = []
        
        source = []
        target = []
        value = []
        link_colors = []
        custom_data = [] # For tooltip strings
        
        # Helper to get index
        def get_idx(name, color):
            if name not in labels:
                labels.append(name)
                node_colors.append(color)
            return labels.index(name)

        # Helper to add link
        def add_link(src_name, src_color, tgt_name, tgt_color, val, link_color=None):
            if val <= 0: return
            s = get_idx(src_name, src_color)
            t = get_idx(tgt_name, tgt_color)
            source.append(s)
            target.append(t)
            value.append(val)
            link_colors.append(link_color if link_color else "rgba(180, 180, 180, 0.5)")
            
            # Format value for tooltip (B or M)
            fmt_val = format_large_number(val)
            custom_data.append(fmt_val)

        # 1. Segments -> Revenue
        segments_total = 0
        try:
            segs = json.loads(segments_json)
            if segs:
                for s in segs:
                    val = float(s['value']) * 1e9 
                    add_link(f"{s['label']}", "#5DADE2", "Total Revenue", COLOR_REV, val, "rgba(93, 173, 226, 0.3)")
                    segments_total += val
        except:
            pass
            
        # 2. Revenue -> COGS & Gross Profit
        add_link("Total Revenue", COLOR_REV, "Cost of Revenue", COLOR_COST, cogs, "rgba(231, 76, 60, 0.3)")
        add_link("Total Revenue", COLOR_REV, "Gross Profit", COLOR_GP, gross_profit, "rgba(40, 180, 99, 0.3)")
        
        # 3. Gross Profit -> OpEx & Op Income
        if rd > 0:
            add_link("Gross Profit", COLOR_GP, "R&D", COLOR_OPEX, rd, "rgba(243, 156, 18, 0.3)")
        if sga > 0:
            add_link("Gross Profit", COLOR_GP, "SG&A", COLOR_OPEX, sga, "rgba(243, 156, 18, 0.3)")
            
        remaining_opex = op_expense - rd - sga
        if remaining_opex > 0:
             add_link("Gross Profit", COLOR_GP, "Other OpEx", COLOR_OPEX, remaining_opex, "rgba(243, 156, 18, 0.3)")
        
        add_link("Gross Profit", COLOR_GP, "Operating Income", COLOR_GP, op_income, "rgba(40, 180, 99, 0.3)")
        
        # 4. Op Income -> Tax & Net Income
        add_link("Operating Income", COLOR_GP, "Tax", COLOR_COST, tax, "rgba(231, 76, 60, 0.3)")
        add_link("Operating Income", COLOR_GP, "Net Income", COLOR_NET, net_income, "rgba(30, 132, 73, 0.5)")
        
        return {
            "label": labels,
            "color": node_colors,
            "source": source,
            "target": target,
            "value": value,
            "link_color": link_colors,
            "custom_data": custom_data
        }

    except Exception as e:
        print(f"Sankey Error: {e}")
        return None
    """
    Summarizes news using Gemini API.
    """
    if not api_key:
        return "Please provide a gemini API Key to see the summary."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')

        
        # Prepare content
        news_text = ""
        for i, item in enumerate(news_items[:7]): # Limit to 7 items
            news_text += f"{i+1}. {item.get('title')} ({item.get('source')}) - {item.get('body')}\n"
            
        prompt = f"""
        You are a financial analyst. Based on the following recent news titles and snippets, provide a concise summary of what is driving the stock's sentiment.
        
        Then, list the top 3 most important articles from the provided list. For each, strictly format it as:
        - **[Title]**: Why it's worth reading.
        
        News Items:
        {news_text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error gathering AI summary: {e}. (Ensure API Key is valid and supports 'gemini-2.0-flash-exp')"

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
    """
    try:
        # Search for earnings take aways (Past Year)
        query = f"{ticker_symbol} earnings analysis bull bear thesis"
        results = DDGS().news(keywords=query, region="us-en", safesearch="off", timelimit="y", max_results=5)
        return results
    except Exception as e:
        print(f"Error searching earnings context: {e}")
        return []

def synthesize_core_focus(ticker, context_results, api_key):
    """
    Synthesizes search results into a 'Core Strategic Focus' summary with Bull/Bear split.
    """
    if not api_key:
        return "Please provide a gemini API Key to see the analysis."
    if not context_results:
        return "No recent earnings analysis found to summarize."
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        context_text = ""
        for item in context_results:
            context_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('body')}\n"
            
        prompt = f"""
        You are a senior investment strategist. Based on the following search results regarding {ticker}'s recent earnings and financial reports:
        
        Provide a balanced strategic view. 
        **Style Guide**: Write in a smooth, professional narrative. **Do not** force numbers if they make the sentence choppy. Instead, weave them naturally into the explanation (e.g., "...driven by a 20% surge in revenue..."). Avoid using asterisks (*) for emphasis inside sentences.
        
        1. **🐂 Bull Case (Optimistic)**: Main argument for buying. Support with specific product success or growth metrics where they fit naturally.
        2. **🐻 Bear Case (Pessimistic)**: Main risk. Support with valuation concerns or margin compression facts.
        3. **🔑 Key Variance**: Where do bulls and bears disagree?

        **Formatting Rules (CRITICAL)**:
        - **NO LaTeX**: Do NOT use `$` signs to wrap sentences or numbers (e.g. `$27.5M profit$`). This destroys spacing.
        - **Currency**: Write "$27.5 billion" or "27.5 billion USD".
        - **Spaces**: Ensure proper spacing between words (e.g., "The 300 Billion" not "The300Billion").

        Context:
        {context_text}
        
        Output format:
        **🐂 Bull Case**: [Narrative paragraph]
        
        **🐻 Bear Case**: [Narrative paragraph]
        
        **🔑 Key Variance**: [1 sentence]
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error synthesizing core focus: {e}"

def search_key_events(ticker_symbol):
    """
    Searches for major events (Past 3 months & Future 3 months).
    """
    try:
        # Search 1: Recent Past
        query_past = f"{ticker_symbol} major corporate events news last 3 months"
        results_past = DDGS().news(keywords=query_past, region="us-en", safesearch="off", max_results=3)
        
        # Search 2: Upcoming Future
        query_future = f"{ticker_symbol} upcoming major events earnings product launch next 3 months"
        results_future = DDGS().news(keywords=query_future, region="us-en", safesearch="off", max_results=3)
        
        # Combine unique results
        all_results = results_past + results_future
        return all_results
    except Exception as e:
        print(f"Error searching key events: {e}")
        return []

def synthesize_key_events(ticker, context_results, api_key):
    """
    Summarizes Major Events (Timeline: Past & Future).
    """
    if not api_key or not context_results:
        return "No major events found."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        context_text = ""
        for item in context_results:
            context_text += f"- Title: {item.get('title')}\n  Date: {item.get('date')}\n  Snippet: {item.get('body')}\n"
            
        prompt = f"""
        Identify the Major Corporate Events for {ticker}.
        Categorize into "Recent" (Past 3 Months) and "Upcoming" (Next 3 Months).
        
        Focus on: Earnings, Product Launches, M&A, FDA approvals, or specific conference dates.
        
        Output format:
        **🕒 Recent Highlights (Past 3 Months)**:
        * **[Date] - [Event]**: [Impact]
        
        **🔮 Upcoming Catalysts (Next 3 Months)**:
        * **[Est. Date] - [Event]**: [Why it matters]

        **Formatting Rules (CRITICAL)**:
        - **NO LaTeX**: Do NOT use `$` to wrap text. 
        - **Currency**: Correct: "$5 Million". Incorrect: "$5 Million$".
        - **Markdown**: Use `**bold**` only for headers/dates.

        If no upcoming events are found, explicit state "No major confirmed upcoming events found."
        
        Context:
        {context_text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error synthesizing key events: {e}"

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

def synthesize_financial_changes(ticker, context_results, api_key):
    """
    Synthesizes reasons behind financial changes.
    """
    if not api_key:
        return "Please provide a gemini API Key to see the analysis."
    if not context_results:
        return "No recent financial analysis found to summarize."
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        context_text = ""
        for item in context_results:
            context_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('body')}\n"
            
        prompt = f"""
        You are a financial analyst. Based on the following search results regarding {ticker}'s recent financial results:
        
        Explain the "WHY" behind the movement of key metrics.
        **CRITICAL**: When discussing financing (Debt, Convertibles, Equity raises), you MUST provide specific facts found in the text:
        - How much was raised? (e.g. $500M)
        - At what price/interest rate? (e.g. converted at $12.50, or 5% coupon)
        - With whom? (if mentioned)

        - With whom? (if mentioned)

        **Formatting Rules (CRITICAL)**:
        - **NO LaTeX**: Do NOT use `$` signs to wrap sentences.
        - **Currency**: Direct format: "$500M" or "500 million USD".
        - **Validation**: Check that spaces exist between all words.
        
        Output format:
        **Revenue Drivers**:
        * [Reason 1]
        
        **Profitability & Margins**:
        * [Reason 1]
        
        **Operating Cash Flow & Capital (Specifics Required)**:
        * [Reason 1 - citing specific amounts/rates]
        
        Context:
        {context_text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error synthesizing financial changes: {e}"

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

def synthesize_revenue_segments(ticker, context_results, api_key):
    """
    Returns JSON string of segment data: [{label, value, growth}].
    """
    if not api_key or not context_results:
        return "[]"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        context_text = ""
        for item in context_results:
            context_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('body')}\n"
            
        prompt = f"""
        You are a data extraction assistant. Based on the following search results for {ticker}:
        
        Extract the most recent Revenue Breakdown by Segment.
        Return ONLY a raw JSON array. No markdown formatting.
        
        Format:
        [
            {{"label": "Segment Name", "value": 12.5, "growth": "+5%"}},
            {{"label": "Segment Name 2", "value": 4.2, "growth": "-2%"}}
        ]
        
        Rules:
        - "value" should be a number (in Billions USD if possible, or relevant scale).
        - If exact value is not found, estimate or use 0.
        - "growth" is the YoY or QoQ change as a string (e.g. "+12%").
        
        Context:
        {context_text}
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return text
    except Exception as e:
        print(f"Error synthesizing segments: {e}")
        return "[]"

def synthesize_core_driver(ticker, context_results, api_key):
    """
    Identifies the single most important stock price mover.
    """
    if not api_key or not context_results:
        return "N/A"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        context_text = ""
        for item in context_results:
            context_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('body')}\n"
            
        prompt = f"""
        Based on the recent news/earnings for {ticker}:
        What is the #1 specific metric or driver currently moving the stock price? (e.g. "AWS Growth Acceleration", "iPhone Cycle strength", "Ad Revenue recovery").
        
        Return ONLY the name of the driver (max 5 words).
        
        Context:
        {context_text}
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "N/A"

    except Exception as e:
        return "N/A"

def synthesize_competitors(ticker, api_key):
    """
    Returns a list of top 3 competitor tickers (e.g. ['MSFT', 'GOOG']).
    """
    if not api_key:
        return []
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        List the top 4 direct public competitors for {ticker}.
        Return ONLY a JSON list of tickers.
        Example: ["COMP1", "COMP2", "COMP3", "COMP4"]
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        tickers = json.loads(text)
        return tickers
    except Exception as e:
        print(f"Error finding competitors: {e}")
        return []

def get_competitor_data(tickers):
    """
    Fetches basic metrics and 3M/6M/12M performance for a list of tickers.
    """
    data = []
    
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            # Fetch 1y history for returns calculation
            hist = stock.history(period="1y")
            
            # Helper for percentage change
            def get_change(days_ago):
                if len(hist) > days_ago:
                    start_price = hist['Close'].iloc[-(days_ago + 1)]
                    curr_price = hist['Close'].iloc[-1]
                    return ((curr_price - start_price) / start_price) * 100
                return 0.0

            # Approximation: 21 trading days/mo
            chg_3m = get_change(63) 
            chg_6m = get_change(126)
            chg_1y = get_change(250) if len(hist) > 240 else 0.0

            data.append({
                "Ticker": t,
                "Name": info.get('shortName', t),
                "Price": info.get('currentPrice', 0),
                "P/E": info.get('trailingPE', 0),
                "Market Cap": info.get('marketCap', 0),
                "3M %": chg_3m,
                "6M %": chg_6m,
                "1Y %": chg_1y
            })
        except Exception as e:
            print(f"Error fetching data for {t}: {e}")
            continue
            
    return pd.DataFrame(data)

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

def get_sankey_data(ticker_symbol, financials, segments_json):
    """
    Prepares node/link data for an Income Statement Sankey Diagram.
    Style: App Economy (Blue Revenue, Green Profit, Red Costs).
    """
    try:
        inc = financials.get('income_stmt', pd.DataFrame())
        if inc.empty:
            return None
        
        # Get most recent quarter label
        col = inc.columns[0]
        recent = inc[col]
        
        # Format date to YYQx (e.g. 2024-09-30 -> 24Q3)
        try:
            date_obj = pd.to_datetime(col)
            quarter = (date_obj.month - 1) // 3 + 1
            period_label = f"{date_obj.year % 100}Q{quarter}"
        except:
            period_label = str(col).split(' ')[0]

        # Extract Core Values (Absolute positives)
        total_rev = abs(recent.get('Total Revenue', 0))
        cogs = abs(recent.get('Cost Of Revenue', 0))
        gross_profit = abs(recent.get('Gross Profit', 0))
        
        # OpEx Breakdown
        op_expense = abs(recent.get('Operating Expense', 0)) 
        rd = abs(recent.get('Research And Development', 0))
         # Fallback if specific lines missing
        if rd == 0:
             rd = 0
             
        sga = abs(recent.get('Selling General And Administration', 0))
        
        op_income = abs(recent.get('Operating Income', 0))
        
        tax = abs(recent.get('Tax Provision', 0))
        net_income = abs(recent.get('Net Income', 0))
        
        # Colors
        COLOR_REV = "#2E86C1" # Blue
        COLOR_COST = "#E74C3C" # Red
        COLOR_GP = "#28B463" # Green
        COLOR_OPEX = "#F39C12" # Orange
        COLOR_NET = "#1E8449" # Dark Green
        COLOR_GREY = "#95A5A6"
        
        # --- Nodes ---
        labels = []
        node_colors = []
        
        source = []
        target = []
        value = []
        link_colors = []
        custom_data = [] # For tooltip strings
        
        # Helper to get index
        def get_idx(name, color):
            if name not in labels:
                labels.append(name)
                node_colors.append(color)
            return labels.index(name)

        # Helper to add link
        def add_link(src_name, src_color, tgt_name, tgt_color, val, link_color=None):
            if val <= 0: return
            s = get_idx(src_name, src_color)
            t = get_idx(tgt_name, tgt_color)
            source.append(s)
            target.append(t)
            value.append(val)
            link_colors.append(link_color if link_color else "rgba(180, 180, 180, 0.5)")
            
            # Format value for tooltip (B or M)
            fmt_val = format_large_number(val)
            custom_data.append(fmt_val)

        # 1. Segments -> Revenue
        segments_total = 0
        try:
            segs = json.loads(segments_json)
            if segs:
                sorted_segs = sorted(segs, key=lambda x: float(x.get('value', 0)), reverse=True)
                for s in sorted_segs:
                    val = float(s['value']) * 1e9 
                    add_link(f"{s['label']}", "#5DADE2", "Total Revenue", COLOR_REV, val, "rgba(93, 173, 226, 0.3)")
                    segments_total += val
        except:
            pass
            
        # 2. Revenue -> COGS & Gross Profit
        add_link("Total Revenue", COLOR_REV, "Cost of Revenue", COLOR_COST, cogs, "rgba(231, 76, 60, 0.3)")
        add_link("Total Revenue", COLOR_REV, "Gross Profit", COLOR_GP, gross_profit, "rgba(40, 180, 99, 0.3)")
        
        # 3. Gross Profit -> OpEx & Op Income
        # Define OpEx nodes first to ensure order? Plotly arranges automatically.
        if rd > 0:
            add_link("Gross Profit", COLOR_GP, "R&D", COLOR_OPEX, rd, "rgba(243, 156, 18, 0.3)")
        if sga > 0:
            add_link("Gross Profit", COLOR_GP, "SG&A", COLOR_OPEX, sga, "rgba(243, 156, 18, 0.3)")
            
        remaining_opex = op_expense - rd - sga
        if remaining_opex > 0:
             add_link("Gross Profit", COLOR_GP, "Other OpEx", COLOR_OPEX, remaining_opex, "rgba(243, 156, 18, 0.3)")
        
        add_link("Gross Profit", COLOR_GP, "Operating Income", COLOR_GP, op_income, "rgba(40, 180, 99, 0.3)")
        
        # 4. Op Income -> Tax & Net Income
        add_link("Operating Income", COLOR_GP, "Tax", COLOR_COST, tax, "rgba(231, 76, 60, 0.3)")
        add_link("Operating Income", COLOR_GP, "Net Income", COLOR_NET, net_income, "rgba(30, 132, 73, 0.5)")
        
        # Format Labels with Value
        formatted_labels = []
        for l in labels:
            formatted_labels.append(l)

        return {
            "period": period_label, # New field
            "label": formatted_labels,
            "color": node_colors,
            "source": source,
            "target": target,
            "value": value,
            "link_color": link_colors,
            "custom_data": custom_data
        }

    except Exception as e:
        print(f"Sankey Error: {e}")
        return None

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
    Fetches historical price data.
    """
    try:
        df = ticker.history(period=period)
        return df
    except Exception as e:
        print(f"Error fetching history: {e}")

def generate_falsifiable_thesis(ticker, context_text, api_key):
    """
    Generates a draft falsifiable thesis based on provided context.
    """
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        You are a disciplined investment strategist who believes in Karl Popper's "Falsifiability".
        
        Based on the following context for {ticker}, generate a DRAFT Investment Thesis.
        
        Context:
        {context_text[:10000]} # Limit context
        
        **Your Goal**:
        Create a thesis that is **NOT** just "it will go up". It must be a specific hypothesis with a "Kill Switch".
        
        **Output Format (JSON only)**:
        {{
            "thesis_statement": "The core argument (e.g. 'Cloud revenue will accelerate due to AI adoption').",
            "falsification_condition": "Specific, measurable event/metric that proves you WRONG (e.g. 'Cloud growth slows below 15% for 2 quarters').",
            "time_horizon": "e.g. 6-12 Months",
            "confidence": 7
        }}
        
        Rules:
        - "falsification_condition" MUST be specific (numbers, specific events), not vague "if bad things happen".
        - Returns ONLY valid JSON.
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data
        
    except Exception as e:
        return {"error": str(e)}

def refine_thesis_text(current_text, current_condition, instruction, api_key):
    """
    Refines the thesis text based on user instruction.
    """
    if not api_key:
        return current_text, current_condition
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        You are an editor for an investment journal.
        
        Current Thesis: "{current_text}"
        Current Kill Switch: "{current_condition}"
        
        User Instruction: "{instruction}" (e.g. "Make it more professional", "Focus more on margins", "Translate to Chinese")
        
        Refine the Thesis and Kill Switch based on the instruction. Keep the core logic unless asked to change it.
        
        Output (JSON):
        {{
            "thesis_statement": "...",
            "falsification_condition": "..."
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data.get("thesis_statement", current_text), data.get("falsification_condition", current_condition)
        
    except Exception as e:
        return current_text, current_condition
        return pd.DataFrame()

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

    return signals

def get_company_branding_keywords(ticker, api_key):
    """
    Uses AI to identify the Company Name and Top 3 Famous Products.
    Returns a list of keywords for filtering.
    """
    if not api_key:
        return []
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        Analyze the stock ticker: {ticker}.
        Identify:
        1. Parent Company Name (e.g. Alphabet Inc.)
        2. Common Colloquial Name (e.g. Google)
        3. Sibling/Dual-Class Tickers (e.g. if GOOG, return GOOGL too).
        4. Top 3 Famous Products (e.g. iPhone, YouTube, Search).

        Return ONLY a comma-separated list of these keywords.
        Example for GOOG: Alphabet, Google, GOOGL, YouTube, Cloud
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        keywords = [k.strip() for k in text.split(',') if k.strip()]
        return keywords
    except Exception as e:
        print(f"Error getting branding keywords: {e}")
        return []

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
            url = "https://gamma-api.polymarket.com/events"
            params = {
                "question": query_term,
                "limit": 20,
                "closed": "false"
            }
            try:
                r = requests.get(url, params=params)
                if r.status_code == 200:
                    return r.json()
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
