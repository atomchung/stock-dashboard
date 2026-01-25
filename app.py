import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils
import json
import theses_manager
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from agent import StockAgent


# Load env vars
load_dotenv()

# Page Configuration
st.set_page_config(page_title="Investment Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Helper Functions ---
def create_compact_bar_chart(x_data, y_data, title, color):
    """
    Creates a compact bar chart with values and QoQ growth.
    """
    final_texts = []
    
    if len(y_data) > 0:
        for i in range(len(y_data)):
            val = y_data.iloc[i]
            val_str = f"{val:,.1f}"
            
            growth_str = ""
            if i > 0:
                prev = y_data.iloc[i-1]
                if prev != 0:
                    pct = ((val - prev) / abs(prev)) * 100
                    emoji = "🔺" if pct > 0 else "🔻"
                    growth_str = f"  ({emoji}{pct:.1f}%)"
                else:
                    growth_str = "  (-)"
            
            final_texts.append(f"{val_str}{growth_str}")

    fig = go.Figure(go.Bar(
        x=x_data, 
        y=y_data, 
        name=title, 
        marker_color=color,
        text=final_texts,
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: %{y:,.1f}<extra></extra>'
    ))
    
    max_val = max(y_data) if len(y_data) > 0 else 0
    min_val = min(y_data) if len(y_data) > 0 else 0

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=30, b=20),
        height=280, 
        yaxis=dict(title="", showticklabels=True, showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis_range=[min_val * 1.1 if min_val < 0 else 0, max_val * 1.25],
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        font=dict(size=10)
    )
    return fig

# --- Page Rendering Functions ---

def render_dashboard(api_key, ticker_symbol):
    
    if 'last_ticker' not in st.session_state:
        st.session_state['last_ticker'] = ""

    # Clear cache if ticker changes
    if ticker_symbol != st.session_state['last_ticker'] and ticker_symbol:
         keys_to_clear = ['news', 'earnings_context', 'evt_context', 'data_loaded', 'ticker_obj', 'info', 'financials', 'history_df', 'signals', 'competitors_list', 'news_summary', 'strategy_summary', 'evt_summary', 'fin_summary']
         for k in keys_to_clear:
             if k in st.session_state:
                 del st.session_state[k]
         st.session_state['last_ticker'] = ticker_symbol
    
    with st.sidebar:
        st.divider()
        st.header("Dashboard Controls")
        get_data_btn = st.button("Get Data", type="primary", key="dash_get_data")
    
    # --- Data Fetching Logic ---
    if get_data_btn:
        with st.spinner(f"Fetching data for {ticker_symbol}..."):
            ticker, error = utils.get_stock_data(ticker_symbol)
            
            if error:
                st.error(f"Error: {error}")
                st.session_state['data_loaded'] = False
            else:
                st.session_state['ticker_obj'] = ticker
                st.session_state['info'] = ticker.info
                st.session_state['news'] = utils.get_news(ticker_symbol) 
                st.session_state['financials'] = utils.get_financials(ticker)
                
                history_df = utils.get_historical_data(ticker)
                st.session_state['history_df'] = utils.calculate_momentum(history_df)
                
                st.session_state['signals'] = utils.analyze_investment_signals(st.session_state['info'], st.session_state['history_df'])
                
                st.session_state['segments_json'] = "[]"
                st.session_state['core_driver'] = "N/A"
                
                if api_key:
                    agent = StockAgent(api_key, ticker_symbol)
                    # st.session_state['agent'] removed to prevent pickling error
                    
                    with st.spinner("Extracting Revenue Segments & Drivers..."):
                        seg_context = utils.search_revenue_segments(ticker_symbol)
                        st.session_state['segments_json'] = agent.extract_revenue_segments(seg_context)
                        st.session_state['core_driver'] = agent.identify_core_driver(st.session_state['news'])

                
                st.session_state['data_loaded'] = True
                st.session_state['current_ticker'] = ticker_symbol

    # --- Dashboard View ---
    if st.session_state.get('data_loaded', False):
        info = st.session_state['info']
        news = st.session_state['news']
        financials = st.session_state['financials']
        history_df = st.session_state['history_df']
        signals = st.session_state['signals']
        segments_json = st.session_state.get('segments_json', '[]')
        core_driver = st.session_state.get('core_driver', 'N/A')
        
        # --- First Screen: Compact & Visual ---
        col_metrics, col_summary = st.columns([1, 2])
        
        with col_metrics:
            curr_price = info.get('currentPrice', 0)
            prev_close = info.get('previousClose', curr_price)
            delta = curr_price - prev_close
            delta_pct = (delta / prev_close) if prev_close else 0
            
            st.metric(label="Current Price", value=f"${curr_price:.2f}", delta=f"{delta:.2f} ({delta_pct*100:.2f}%)")
            st.write(f"**Range:** ${info.get('dayLow', 0)} - ${info.get('dayHigh', 0)}")
            
            vol_str = utils.format_large_number(info.get('volume', 0))
            st.write(f"**Vol:** {vol_str}")
            
        with col_summary:
            st.subheader("💡 Analysis")
            cols = st.columns(len(signals))
            for idx, s in enumerate(signals):
                    st.write(s)
            
            if api_key and core_driver != "N/A":
                st.info(f"**🎯 Core Price Driver:** {core_driver}")
        
        st.divider()

        # --- Technical Overview ---
        if not history_df.empty:
            st.subheader("Technical Overview")
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, 
                                row_heights=[0.5, 0.2, 0.3],
                                subplot_titles=("Price Trend (SMA 50/200)", "Volume", "Momentum (RSI)"))

            fig.add_trace(go.Candlestick(x=history_df.index,
                            open=history_df['Open'], high=history_df['High'],
                            low=history_df['Low'], close=history_df['Close'], name='Price'), row=1, col=1)
            fig.add_trace(go.Scatter(x=history_df.index, y=history_df['SMA_50'], line=dict(color='orange', width=1), name='SMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=history_df.index, y=history_df['SMA_200'], line=dict(color='blue', width=1), name='SMA 200'), row=1, col=1)

            colors = ['green' if row['Open'] - row['Close'] >= 0 else 'red' for index, row in history_df.iterrows()]
            fig.add_trace(go.Bar(x=history_df.index, y=history_df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

            fig.add_trace(go.Scatter(x=history_df.index, y=history_df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            fig.update_layout(height=800, xaxis_rangeslider_visible=False, showlegend=False)
            fig.update_yaxes(title_text="Price", row=1, col=1)
            fig.update_yaxes(title_text="Vol", row=2, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
            st.plotly_chart(fig, use_container_width=True)

        if api_key:
            st.divider()
            st.subheader("🧠 Core Strategic Focus (Bull vs Bear)")
            if 'strategy_summary' not in st.session_state:
                 agent = StockAgent(api_key, ticker_symbol)
                 with st.spinner("Synthesizing Strategy (Bull/Bear)..."):
                     context = utils.search_earnings_context(ticker_symbol)
                     # Pass company info and news for better context
                     company_info = st.session_state.get('info', {})
                     news_context = st.session_state.get('news', [])
                     st.session_state['strategy_summary'] = agent.analyze_strategy(context, news_context, company_info)

            st.markdown(st.session_state['strategy_summary'])

        st.divider()

        tab_news, tab_fin, tab_comp, tab_thesis = st.tabs(["📰 AI News Insights", "💰 Financials Deep Dive", "⚔️ Competitors", "🧘 Thesis Tracker"])
        
        with tab_news:
            if api_key:
                st.subheader("🤖 AI Executive Summary")
                with st.spinner("Generating AI News Summary..."):
                    agent = StockAgent(api_key, ticker_symbol)
                    if 'news_summary' not in st.session_state:
                         st.session_state['news_summary'] = agent.analyze_news(news)
                    st.markdown(st.session_state['news_summary'])
                
                st.divider()
                st.subheader("🗓️ Major Events Timeline (Past & Future)")
                with st.spinner("Identifying Key Events & Catalysts..."):
                     if 'evt_summary' not in st.session_state:
                          evt_context = utils.search_key_events(ticker_symbol)
                          st.session_state['evt_summary'] = agent.analyze_events(evt_context)
                     st.markdown(st.session_state['evt_summary'])

                     
            else:
                st.warning("⚠️ Enter Gemini API Key in sidebar to unlock AI Summary.")
            
            st.divider()
            st.subheader("🎲 Prediction Markets (Polymarket)")
            with st.spinner("Fetching Betting Markets..."):
                extra_kws = []
                if api_key:
                    agent = StockAgent(api_key, ticker_symbol)
                    extra_kws = agent.get_branding_keywords()
                
                poly_markets = utils.get_polymarket_data(ticker_symbol, info.get('shortName'), extra_kws)

                
                if poly_markets:
                    for m in poly_markets:
                        st.markdown(f"**[{m['title']}]({m['url']})**")
                        c1, c2 = st.columns([1, 2])
                        c1.caption(f"💴 Volume: ${utils.format_large_number(m['volume'])}")
                        c2.caption(f"📊 Odds: {m['odds']}")
                else:
                    st.info("No active prediction markets found for this ticker.")
            
            st.divider()
            st.subheader("Latest Articles (最新文章)")
            if news:
                for item in news[:5]:
                    title = item.get('title', 'No Title')
                    url = item.get('url', '#')
                    source = item.get('source', 'Unknown Source')
                    date = item.get('date', '')
                    st.markdown(f"• **[{title}]({url})**")
                    st.caption(f"{source} | {date}")
            else:
                st.write("No recent articles found.")

        with tab_fin:
            st.header("Quarterly Performance")
            st.caption("All values in USD. 'M' = Millions, 'B' = Billions.")
            
            m1, m2, m3, m4 = st.columns(4)
            
            mcap = utils.format_large_number(info.get('marketCap', 0))
            gross_profit_val = info.get('grossProfits', 0)
            gross_profit = utils.format_large_number(gross_profit_val) if 'grossProfits' in info else "N/A"
            
            m1.metric("Market Cap", mcap)
            m2.metric("Basic EPS", f"{info.get('trailingEps', 'N/A')}")
            m3.metric("Gross Profit (TTM)", gross_profit)
            m4.metric("Revenue Growth", f"{info.get('revenueGrowth', 0)*100:.2f}%" if info.get('revenueGrowth') else "N/A")

            st.divider()
            
            inc_stmt = financials.get('income_stmt', pd.DataFrame())
            cash_flow = financials.get('cashflow', pd.DataFrame())
            
            if not inc_stmt.empty:
                num_cols = min(len(inc_stmt.columns), 5)
                cols = inc_stmt.columns[:num_cols][::-1]
                dates = [d.strftime('%Y-%m') if hasattr(d, 'strftime') else str(d) for d in cols]
                
                df_inc = inc_stmt[cols]
                df_cf = cash_flow[cols] if not cash_flow.empty else pd.DataFrame()
                
                try:
                    revenue = df_inc.loc['Total Revenue'] if 'Total Revenue' in df_inc.index else df_inc.iloc[0]
                    
                    if 'EBITDA' in df_inc.index:
                        ebitda = df_inc.loc['EBITDA']
                    elif 'Normalized EBITDA' in df_inc.index:
                        ebitda = df_inc.loc['Normalized EBITDA']
                    else:
                        ebitda = df_inc.loc['Operating Income'] if 'Operating Income' in df_inc.index else pd.Series([0]*num_cols)
                        
                    if not df_cf.empty:
                            op_cash_flow = df_cf.loc['Operating Cash Flow'] if 'Operating Cash Flow' in df_cf.index else pd.Series([0]*num_cols)
                            capex_row = None
                            for idx in df_cf.index:
                                if "Capital" in idx and "Expenditure" in idx:
                                    capex_row = df_cf.loc[idx]
                                    break
                            capex = capex_row if capex_row is not None else pd.Series([0]*num_cols)
                            capex = capex.abs()
                    else:
                            op_cash_flow = pd.Series([0]*num_cols)
                            capex = pd.Series([0]*num_cols)

                    agent = StockAgent(api_key, ticker_symbol) if api_key else None
                    sankey_data = utils.get_sankey_data(ticker_symbol, financials, segments_json, agent=agent)
                    if sankey_data:
                        period_label = sankey_data.get('period', 'Most Recent Quarter')
                        st.subheader(f"🌊 Income Statement Flow ({period_label})")
                        
                        fig_sankey = go.Figure(data=[go.Sankey(
                            node = dict(
                                pad = 30,
                                thickness = 20,
                                line = dict(color = "black", width = 0.5),
                                label = sankey_data['label'],
                                color = sankey_data['color'],
                                hovertemplate='<b>%{label}</b><extra></extra>' 
                            ),
                            link = dict(
                                source = sankey_data['source'],
                                target = sankey_data['target'],
                                value = sankey_data['value'],
                                color = sankey_data['link_color'],
                                customdata = sankey_data.get('custom_data', [utils.format_large_number(x) for x in sankey_data['value']]),
                                hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>Value: %{customdata}<extra></extra>'
                            ))])
                        
                        fig_sankey.update_layout(title_text=f"{ticker_symbol} Financial Flow (USD)", font_size=12, height=500)
                        st.plotly_chart(fig_sankey, use_container_width=True)
                    else:
                        st.info("Insufficient data for Sankey Diagram.")

                    st.subheader("Quarterly Trends (Millions USD)")
                    
                    def plot_metric(dates, values, name, color):
                        try:
                            values = pd.to_numeric(values, errors='coerce')
                            if values.dropna().empty: return None
                            values_m = values / 1e6
                            return create_compact_bar_chart(dates, values_m, f"{name} ($M)", color)
                        except Exception as e:
                            return None

                    fig = plot_metric(dates, revenue, "Revenue", '#2E86C1')
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
                    gp_series = pd.Series([0]*len(dates))
                    if 'Gross Profit' in df_inc.index:
                        gp_series = df_inc.loc['Gross Profit']
                    
                    fig = plot_metric(dates, gp_series, "Gross Profit", '#28B463')
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
                    fig = plot_metric(dates, ebitda, "EBITDA", '#27AE60')
                    if fig: st.plotly_chart(fig, use_container_width=True)

                    fig = plot_metric(dates, op_cash_flow, "Operating Cash Flow", '#F1C40F')
                    if fig: st.plotly_chart(fig, use_container_width=True)
                    
                    fig = plot_metric(dates, capex, "Capital Expenditure", '#E74C3C')
                    if fig: st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Could not calculate specific metrics: {e}")
            else:
                st.write("No quarterly income statement data available.")
            
            if api_key:
                st.divider()
                st.subheader("📉 Financial Performance Deep Dive (AI)")
                with st.spinner("Analyzing financial drivers..."):
                    agent = StockAgent(api_key, ticker_symbol)
                    if 'fin_summary' not in st.session_state:
                         fin_context = utils.search_financial_analysis(ticker_symbol)
                         st.session_state['fin_summary'] = agent.analyze_financials(fin_context)

                    st.markdown(st.session_state['fin_summary'])
        
        with tab_comp:
            st.subheader(f"Competitor Analysis ({ticker_symbol})")
            
            if api_key:
                with st.spinner("Analyzing competitors..."):
                    agent = StockAgent(api_key, ticker_symbol)
                    if 'competitors_list' not in st.session_state:
                         st.session_state['competitors_list'] = agent.identify_competitors()

                    
                    comp_list = st.session_state['competitors_list']
                    
                    if not comp_list:
                        st.warning(f"⚠️ Could not identify relevant industry peers for {ticker_symbol}. This may be a niche company with few public competitors.")
                        # Only show the target stock itself
                        all_tickers = [ticker_symbol]
                    else:
                        all_tickers = [ticker_symbol] + comp_list
                
                st.caption("Key Valuation & Performance Metrics")
                comp_df = utils.get_competitor_data(all_tickers)
                if not comp_df.empty:
                    st.dataframe(
                        comp_df.style.format({
                            "Price": "${:.2f}",
                            "P/E": "{:.1f}x",
                            "Market Cap": lambda x: utils.format_large_number(x),
                            "3M %": "{:+.2f}%",
                            "6M %": "{:+.2f}%",
                            "1Y %": "{:+.2f}%"
                        }).map(lambda v: 'color: green' if v > 0 else 'color: red', subset=["3M %", "6M %", "1Y %"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("Could not find competitors or fetch their data.")
                
                st.caption("12-Month Relative Performance (%)")
                hist_df = utils.get_competitor_history(all_tickers)
                if not hist_df.empty:
                    fig_perf = go.Figure()
                    for col in hist_df.columns:
                        width = 3 if col == ticker_symbol else 1.5
                        opacity = 1.0 if col == ticker_symbol else 0.7
                        
                        fig_perf.add_trace(go.Scatter(
                            x=hist_df.index, 
                            y=hist_df[col], 
                            mode='lines', 
                            name=col,
                            line=dict(width=width),
                            opacity=opacity
                        ))
                    fig_perf.update_layout(xaxis_title="Date", yaxis_title="Return (%)", hovermode="x unified")
                    st.plotly_chart(fig_perf, use_container_width=True)
                else:
                    st.warning("Could not fetch historical data for comparison.")
            else:
                st.warning("⚠️ Enter Gemini API Key to enable Competitor Analysis.")

        with tab_thesis:
            st.header("Investment Thesis Journal")
            st.caption("“The most dangerous investment is the one that ‘cannot be wrong’.” — Define your kill switch.")

            col_draft, col_journal = st.columns([1, 1])

            with col_draft:
                st.subheader("📝 Draft New Thesis")
                if 'draft_thesis_id' not in st.session_state:
                        st.session_state['draft_thesis_id'] = ""
                
                if "draft_fn_statement" not in st.session_state: st.session_state["draft_fn_statement"] = ""
                if "draft_fn_condition" not in st.session_state: st.session_state["draft_fn_condition"] = ""
                if "draft_fn_horizon" not in st.session_state: st.session_state["draft_fn_horizon"] = "3-6 Months"
                if "draft_fn_confidence" not in st.session_state: st.session_state["draft_fn_confidence"] = 5

                if api_key:
                    st.caption("ℹ️ Based on **News Insights** & optional keywords.")
                    c_gen_1, c_gen_2 = st.columns([3, 1])
                    user_keywords = c_gen_1.text_input("Keywords / Focus (Optional)", placeholder="e.g. 'Focus on AI capex', 'Bear case'", key="ai_focus_kws")
                    
                    if c_gen_2.button("✨ Auto-Generate"):
                         with st.spinner("Generating Draft..."):
                             ctx = ""
                             if st.session_state.get('news'):
                                 if 'news_summary' in st.session_state:
                                     ctx += f"News Summary: {st.session_state['news_summary']}\n"
                                 else:
                                     agent = StockAgent(api_key, ticker_symbol)
                                     ctx += f"News Summary: {agent.analyze_news(news)}\n"
                             
                             if user_keywords:
                                 ctx += f"\nUser Focus/Keywords: {user_keywords}\n"
                                 
                             agent = StockAgent(api_key, ticker_symbol)
                             generated = agent.generate_thesis(ctx, user_keywords)

                             
                             if generated and "error" not in generated:
                                st.session_state["draft_fn_statement"] = generated.get("thesis_statement", "")
                                st.session_state["draft_fn_condition"] = generated.get("falsification_condition", "")
                                st.session_state["draft_fn_confidence"] = int(generated.get("confidence", 5))
                                h = generated.get("time_horizon", "3-6 Months") 
                                if h not in ["1-3 Months", "3-6 Months", "6-12 Months", "1+ Year"]: h = "3-6 Months"
                                st.session_state["draft_fn_horizon"] = h
                                st.success("Draft generated!")
                             else:
                                st.error(f"Generation failed: {generated.get('error') if generated else 'Unknown'}")

                st.text_area("Thesis Statement (Why?)", key="draft_fn_statement", height=150)
                st.text_area("Falsification Condition (Kill Switch)", key="draft_fn_condition", height=100, help="Specific event or metric that invalidates this thesis.")
                
                c1, c2 = st.columns(2)
                c1.selectbox("Time Horizon", ["1-3 Months", "3-6 Months", "6-12 Months", "1+ Year"], key="draft_fn_horizon")
                c2.slider("Confidence Level", 1, 10, key="draft_fn_confidence")

                def on_save_thesis():
                    if not st.session_state["draft_fn_statement"] or not st.session_state["draft_fn_condition"]:
                        st.session_state['save_error'] = "Please fill in both Statement and Condition."
                    else:
                        thesis_to_save = {
                            "id": st.session_state['draft_thesis_id'], 
                            "ticker": ticker_symbol,
                            "thesis_statement": st.session_state["draft_fn_statement"],
                            "falsification_condition": st.session_state["draft_fn_condition"],
                            "time_horizon": st.session_state["draft_fn_horizon"],
                            "confidence": st.session_state["draft_fn_confidence"],
                            "status": "Active"
                        }
                        success, msg = theses_manager.save_thesis(thesis_to_save)
                        if success:
                            st.session_state['save_success'] = "Saved!"
                            st.session_state["draft_fn_statement"] = ""
                            st.session_state["draft_fn_condition"] = ""
                            st.session_state["draft_fn_confidence"] = 5
                            st.session_state["draft_thesis_id"] = ""
                        else:
                            st.session_state['save_error'] = f"Save failed: {msg}"

                st.button("💾 Save to Journal", type="primary", on_click=on_save_thesis)
                
                if 'save_error' in st.session_state:
                    st.error(st.session_state['save_error'])
                    del st.session_state['save_error']
                if 'save_success' in st.session_state:
                    st.success(st.session_state['save_success'])
                    del st.session_state['save_success']

            with col_journal:
                st.subheader(f"📖 Active Theses for {ticker_symbol}")
                all_theses = theses_manager.load_theses() or []
                my_theses = [t for t in all_theses if t['ticker'] == ticker_symbol]
                
                if not my_theses:
                    st.info("No active theses for this stock.")
                
                for t in my_theses:
                    with st.container(border=True):
                        st.markdown(f"**🔭 {t['thesis_statement']}**")
                        st.warning(f"**☠️ Kill Switch**: {t['falsification_condition']}")
                        st.caption(f"📅 {t['time_horizon']} | 💪 Conf: {t['confidence']}/10 | Created: {t.get('created_at', 'N/A')}")
                        
                        c1, c2 = st.columns([1, 5])
                        if c1.button("🗑️", key=f"del_{t['id']}"):
                            theses_manager.delete_thesis(t['id'])
                            st.experimental_rerun()
                            
                        if c2.button("Edit", key=f"edit_{t['id']}"):
                            st.session_state["draft_fn_statement"] = t["thesis_statement"]
                            st.session_state["draft_fn_condition"] = t["falsification_condition"]
                            st.session_state["draft_fn_horizon"] = t["time_horizon"]
                            st.session_state["draft_fn_confidence"] = int(t["confidence"])
                            st.session_state["draft_thesis_id"] = t["id"]
                            st.experimental_rerun()
    else:
        st.info("Enter a stock ticker and click 'Get Data' to start.")

def render_journal(api_key):
    """
    Renders the Global Investment Journal with inline editing.
    """
    st.header("📖 Global Investment Journal")

    # Load all data
    all_theses = theses_manager.load_theses() or []
    
    if not all_theses:
        st.info("No investment theses found. Go to 'Stock Dashboard' to create one!")
        return

    # Filter / Search
    filter_ticker = st.text_input("Filter by Ticker", "").upper()
    if filter_ticker:
        all_theses = [t for t in all_theses if filter_ticker in t['ticker']]
    
    st.divider()
    
    # Display as Cards (Iterate)
    for t in all_theses:
        status_icon = "✅" if t.get('status')=='Active' else "🏁"
        
        # Calculate Date Logic
        created_str = t.get('created_at', '')
        verification_date_str = "N/A"
        
        if created_str:
            try:
                # Assuming format %Y-%m-%d %H:%M:%S
                created_dt = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
                created_display = created_dt.strftime("%Y-%m-%d")
                
                # Estimate verification date from horizon
                horizon_map = {
                    "1-3 Months": 90,
                    "3-6 Months": 180,
                    "6-12 Months": 365,
                    "1+ Year": 365 # Default to 1Y
                }
                days = horizon_map.get(t['time_horizon'], 180)
                verif_dt = created_dt + timedelta(days=days)
                verification_date_str = verif_dt.strftime("%Y-%m-%d")
                
                # Colors for urgency
                days_left = (verif_dt - datetime.now()).days
                if days_left < 0:
                    verif_color = "red"
                    verif_label = f"{verification_date_str} (Expired)"
                elif days_left < 30:
                    verif_color = "orange"
                    verif_label = f"{verification_date_str} ({days_left} days left)"
                else:
                    verif_color = "green"
                    verif_label = f"{verification_date_str}"
                    
            except:
                created_display = created_str
                verif_label = "Unknown"
                verif_color = "gray"
        else:
            created_display = "N/A"
            verif_label = "N/A"
            verif_color = "gray"

        # Check Edit Mode
        is_editing = st.session_state.get(f"edit_mode_{t['id']}", False)
        
        with st.expander(f"{t['ticker']} | 📅 Created: {created_display} | 🎯 Check By: {verif_label}", expanded=True):
            if is_editing:
                # Edit Mode Inputs
                new_statement = st.text_area("Thesis", t['thesis_statement'], key=f"e_s_{t['id']}")
                new_condition = st.text_area("Kill Switch", t['falsification_condition'], key=f"e_c_{t['id']}")
                
                c_e1, c_e2 = st.columns(2)
                # Horizon index safety
                h_opts = ["1-3 Months", "3-6 Months", "6-12 Months", "1+ Year"]
                curr_h_idx = h_opts.index(t['time_horizon']) if t['time_horizon'] in h_opts else 1
                
                new_horizon = c_e1.selectbox("Horizon", h_opts, index=curr_h_idx, key=f"e_h_{t['id']}")
                new_conf = c_e2.slider("Confidence", 1, 10, int(t['confidence']), key=f"e_cf_{t['id']}")
                
                # Save / Cancel
                ca, cb = st.columns([1, 1])
                if ca.button("💾 Save", key=f"save_{t['id']}"):
                    updated_thesis = t.copy()
                    updated_thesis.update({
                        "thesis_statement": new_statement,
                        "falsification_condition": new_condition,
                        "time_horizon": new_horizon,
                        "confidence": new_conf
                    })
                    theses_manager.save_thesis(updated_thesis)
                    st.session_state[f"edit_mode_{t['id']}"] = False
                    st.experimental_rerun()
                    
                if cb.button("❌ Cancel", key=f"cancel_{t['id']}"):
                    st.session_state[f"edit_mode_{t['id']}"] = False
                    st.experimental_rerun()
            else:
                # View Mode - Visual Enhancement
                
                # 1. Ticker as Title
                st.title(f"{t['ticker']}")
                
                # 2. Metadata line
                st.caption(f"📅 Created: {created_display} | 🎯 Check By: :{verif_color}[{verif_label}] | ⏳ Horizon: {t['time_horizon']} | 💪 Conf: {t['confidence']}/10")
                
                st.divider()
                
                # 3. Sections as Subheaders & Content as Normal Text
                st.subheader("🔭 Thesis")
                st.write(t['thesis_statement'])
                
                st.subheader("☠️ Falsification Condition (Kill Switch)")
                st.write(t['falsification_condition'])
                
                st.divider()
                
                # Actions
                ca, cb = st.columns([1, 4])
                if ca.button("Delete", key=f"j_del_{t['id']}"):
                    theses_manager.delete_thesis(t['id'])
                    st.experimental_rerun()
                    
                if cb.button("Edit", key=f"j_edit_{t['id']}"):
                    st.session_state[f"edit_mode_{t['id']}"] = True
                    st.experimental_rerun()

def main():
    st.title("📈 Investment Dashboard Pro")
    
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Stock Dashboard", "Investment Journal"])
        st.divider()
    
        st.header("Global Settings")
        env_key = os.getenv("GEMINI_API_KEY", "")
        api_key = st.text_input("Gemini API Key", value=env_key, type="password", key="global_api_key")
        st.info("💡 Providing an API Key enables AI news & strategy analysis.")
    
    if page == "Stock Dashboard":
        with st.sidebar:
             default_ticker = st.session_state.get('last_ticker', 'NVDA') or 'NVDA'
             ticker = st.text_input("Enter Stock Ticker", value=default_ticker).upper()
             
        render_dashboard(api_key, ticker)
        
    elif page == "Investment Journal":
        render_journal(api_key)

if __name__ == "__main__":
    main()
