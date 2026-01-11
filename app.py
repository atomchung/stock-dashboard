import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import utils
import json

import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Page Configuration
st.set_page_config(page_title="Investment Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title("📈 Investment Dashboard Pro")

# Sidebar for Inputs
with st.sidebar:
    st.header("Settings")
    ticker_symbol = st.text_input("Enter Stock Ticker", value="AAPL").upper()
    
    # Auto-load key
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key (for AI Insights)", value=env_key, type="password")
    
    get_data_btn = st.button("Get Data", type="primary")
    
    st.info("💡 Providing an API Key enables AI news & strategy analysis.")

def create_compact_bar_chart(dates, values, title, color):
    """
    Helper to create a compact bar chart with growth annotations and clean tooltips.
    """
    # Calculate Growth
    growth_texts = []
    for i in range(len(values)):
        if i == 0:
            growth_texts.append("")
        else:
            prev = values[i-1]
            curr = values[i]
            if prev != 0:
                pct = ((curr - prev) / abs(prev)) * 100
                symbol = "+" if pct >= 0 else ""
                growth_texts.append(f"{symbol}{pct:.1f}%")
            else:
                growth_texts.append("N/A")

    fig = go.Figure(go.Bar(
        x=dates, 
        y=values, 
        name=title, 
        marker_color=color,
        text=growth_texts,
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: %{y:.1f}<extra></extra>' # Clean tooltip
    ))
    
    # Increase Y-axis range slightly to fit text
    max_val = max(values) if len(values) > 0 else 0
    min_val = min(values) if len(values) > 0 else 0
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        margin=dict(l=20, r=20, t=30, b=20),
        height=280, 
        yaxis=dict(title="", showticklabels=True),
        yaxis_range=[min_val * 1.1 if min_val < 0 else 0, max_val * 1.25] 
    )
    return fig

if get_data_btn:
    with st.spinner(f"Fetching data for {ticker_symbol}..."):
        ticker, error = utils.get_stock_data(ticker_symbol)
        
        if error:
            st.error(f"Error: {error}")
        else:
            # Fetch all data
            info = ticker.info
            news = utils.get_news(ticker_symbol) 
            financials = utils.get_financials(ticker)
            history_df = utils.get_historical_data(ticker, period="1y")
            history_df = utils.calculate_momentum(history_df)
            signals = utils.analyze_investment_signals(info, history_df)
            
            # --- AI Extractions (Segments & Driver) ---
            segments_json = "[]"
            core_driver = "N/A"
            if api_key:
                with st.spinner("Extracting Revenue Segments & Drivers..."):
                    seg_context = utils.search_revenue_segments(ticker_symbol)
                    segments_json = utils.synthesize_revenue_segments(ticker_symbol, seg_context, api_key)
                    # Use news context for core driver as it reflects current sentiment
                    core_driver = utils.synthesize_core_driver(ticker_symbol, news, api_key)
            
            # --- First Screen: Compact & Visual ---
            
            # Row 1: Key Metrics & AI Summary/Signals
            col_metrics, col_summary = st.columns([1, 2])
            
            with col_metrics:
                # Big Price Display
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
                # Signals
                cols = st.columns(len(signals))
                for idx, s in enumerate(signals):
                     st.write(s)
                
                if api_key and core_driver != "N/A":
                    st.info(f"**🎯 Core Price Driver:** {core_driver}")
            
            st.divider()

            # --- Technical Overview ---
            if not history_df.empty:
                st.subheader("Technical Overview")
                
                # Create subplot with 3 rows: Price (Main), Volume (Small), RSI (Medium)
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, 
                                    row_heights=[0.5, 0.2, 0.3],
                                    subplot_titles=("Price Trend (SMA 50/200)", "Volume", "Momentum (RSI)"))

                # 1. Price
                fig.add_trace(go.Candlestick(x=history_df.index,
                                open=history_df['Open'], high=history_df['High'],
                                low=history_df['Low'], close=history_df['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=history_df.index, y=history_df['SMA_50'], line=dict(color='orange', width=1), name='SMA 50'), row=1, col=1)
                fig.add_trace(go.Scatter(x=history_df.index, y=history_df['SMA_200'], line=dict(color='blue', width=1), name='SMA 200'), row=1, col=1)

                # 2. Volume
                colors = ['green' if row['Open'] - row['Close'] >= 0 else 'red' for index, row in history_df.iterrows()]
                fig.add_trace(go.Bar(x=history_df.index, y=history_df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

                # 3. RSI
                fig.add_trace(go.Scatter(x=history_df.index, y=history_df['RSI'], line=dict(color='purple', width=1.5), name='RSI'), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
                
                fig.update_layout(height=800, xaxis_rangeslider_visible=False, showlegend=False)
                fig.update_yaxes(title_text="Price", row=1, col=1)
                fig.update_yaxes(title_text="Vol", row=2, col=1)
                fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
                st.plotly_chart(fig, use_container_width=True)

            # --- AI Strategy Section ---
            if api_key:
                st.divider()
                st.subheader("🧠 Core Strategic Focus (Bull vs Bear)")
                with st.spinner("Synthesizing Strategy (Bull/Bear)..."):
                     context = utils.search_earnings_context(ticker_symbol)
                     strategy_summary = utils.synthesize_core_focus(ticker_symbol, context, api_key)
                     st.markdown(strategy_summary)

            st.divider()

            # --- Tabs: News, Financials, Competitors ---
            tab_news, tab_fin, tab_comp = st.tabs(["📰 AI News Insights", "💰 Financials Deep Dive", "⚔️ Competitors"])
            
            # --- Tab 1: AI News ---
            with tab_news:
                if api_key:
                    st.subheader("🤖 AI Executive Summary")
                    with st.spinner("Generating AI News Summary..."):
                        summary = utils.summarize_news_with_ai(news, api_key)
                        st.markdown(summary)
                else:
                    st.warning("⚠️ Enter Gemini API Key in sidebar to unlock AI Summary.")
                
                st.divider()
                st.subheader("Latest Articles")
                for item in news[:5]: # Show top 5
                    st.markdown(f"**[{item.get('title')}]({item.get('url')})**")
                    st.caption(f"{item.get('source')} | {item.get('date')}")

            # --- Tab 2: Visual Financials ---
            with tab_fin:
                st.header("Quarterly Performance")
                st.caption("All values in USD. 'M' = Millions, 'B' = Billions.")
                
                # New Metrics Display with Formatting
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
                    # Filter up to last 5 columns (quarters) and reverse (Old -> New)
                    num_cols = min(len(inc_stmt.columns), 5)
                    cols = inc_stmt.columns[:num_cols][::-1]
                    dates = [d.strftime('%Y-%m') if hasattr(d, 'strftime') else str(d) for d in cols]
                    
                    df_inc = inc_stmt[cols]
                    df_cf = cash_flow[cols] if not cash_flow.empty else pd.DataFrame()
                    
                    try:
                        # Extract Rows
                        revenue = df_inc.loc['Total Revenue'] if 'Total Revenue' in df_inc.index else df_inc.iloc[0]
                        
                        # EBITDA Extraction
                        if 'EBITDA' in df_inc.index:
                            ebitda = df_inc.loc['EBITDA']
                        elif 'Normalized EBITDA' in df_inc.index:
                            ebitda = df_inc.loc['Normalized EBITDA']
                        else:
                            ebitda = df_inc.loc['Operating Income'] if 'Operating Income' in df_inc.index else pd.Series([0]*num_cols)
                            
                        # Op Cash Flow & CapEx
                        if not df_cf.empty:
                             op_cash_flow = df_cf.loc['Operating Cash Flow'] if 'Operating Cash Flow' in df_cf.index else pd.Series([0]*num_cols)
                             # CapEx is usually 'Capital Expenditure' or 'Capital Expenditures' or 'CapitalExpenditures'
                             # yfinance is inconsistent. Sometimes 'Capital Expenditure'
                             capex_row = None
                             for idx in df_cf.index:
                                 if "Capital" in idx and "Expenditure" in idx:
                                     capex_row = df_cf.loc[idx]
                                     break
                             capex = capex_row if capex_row is not None else pd.Series([0]*num_cols)
                             capex = capex.abs() # Display as positive for chart
                        else:
                             op_cash_flow = pd.Series([0]*num_cols)
                             capex = pd.Series([0]*num_cols)

                        # --- Sankey Diagram (Financial Flow) ---
                        st.subheader("🌊 Income Statement Flow (Most Recent Quarter)")
                        sankey_data = utils.get_sankey_data(ticker_symbol, financials, segments_json)
                        if sankey_data:
                            fig_sankey = go.Figure(data=[go.Sankey(
                                node = dict(
                                  pad = 15,
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
                            
                            fig_sankey.update_layout(title_text=f"{ticker_symbol} Financial Flow (USD)", font_size=10, height=500)
                            st.plotly_chart(fig_sankey, use_container_width=True)
                        else:
                            st.info("Insufficient data for Sankey Diagram.")

                        # --- Separate Compact Charts ---
                        st.subheader("Quarterly Trends (Millions USD)")
                        
                        # Scale to Millions
                        rev_m = revenue / 1e6
                        ebitda_m = ebitda / 1e6
                        ocf_m = op_cash_flow / 1e6
                        capex_m = capex / 1e6

                        # 1. Revenue
                        fig_rev = create_compact_bar_chart(dates, rev_m, "Revenue ($M)", '#2E86C1')
                        st.plotly_chart(fig_rev, use_container_width=True)
                        
                        # 2. EBITDA
                        fig_ebitda = create_compact_bar_chart(dates, ebitda_m, "EBITDA ($M)", '#28B463')
                        st.plotly_chart(fig_ebitda, use_container_width=True)

                        # 3. Operating Cash Flow
                        fig_ocf = create_compact_bar_chart(dates, ocf_m, "Operating Cash Flow ($M)", '#F1C40F')
                        st.plotly_chart(fig_ocf, use_container_width=True)
                        
                        # 4. CapEx (New)
                        fig_capex = create_compact_bar_chart(dates, capex_m, "Capital Expenditure ($M)", '#E74C3C')
                        st.plotly_chart(fig_capex, use_container_width=True)

                    except Exception as e:
                        st.error(f"Could not calculate specific metrics: {e}")
                else:
                    st.write("No quarterly income statement data available.")
                
                # --- AI Financial Analysis ---
                if api_key:
                    st.divider()
                    st.subheader("📉 Financial Performance Deep Dive (AI)")
                    with st.spinner("Analyzing financial drivers..."):
                        fin_context = utils.search_financial_analysis(ticker_symbol)
                        fin_summary = utils.synthesize_financial_changes(ticker_symbol, fin_context, api_key)
                        st.markdown(fin_summary)
            
            # --- Tab 3: Competitors ---
            with tab_comp:
                st.subheader(f"Competitor Analysis ({ticker_symbol})")
                
                if api_key:
                    # Combine current ticker with competitors
                    all_tickers = [ticker_symbol] + competitors_list
                    
                    # 1. Metrics Table
                    st.caption("Key Valuation & Performance Metrics")
                    comp_df = utils.get_competitor_data(all_tickers)
                    if not comp_df.empty:
                        # Formatting
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
                    
                    # 2. Relative Performance Chart
                    st.caption("12-Month Relative Performance (%)")
                    hist_df = utils.get_competitor_history(all_tickers)
                    if not hist_df.empty:
                        fig_perf = go.Figure()
                        for col in hist_df.columns:
                            # Highlight main ticker
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

else:
    st.info("Enter a stock ticker and click 'Get Data' to start.")
