# AI-Powered Investment Dashboard 📈

A comprehensive stock analysis dashboard built with **Streamlit** and **Python**, leveraging **Google Gemini AI** for intelligent financial insights.

## Features

### 1. 📊 Real-Time Market Data
- Live stock prices and historical data via `yfinance`.
- **Interactive Charts**:
    - **Quarterly Trends**: Revenue, EBITDA, Operating Cash Flow, and CapEx (scaled to Millions/Billions).
    - **Volume Analysis**: Price vs. Volume with Moving Averages.
    - **Sankey Diagram**: Visualizes the flow from Revenue to Net Income (Income Statement).

### 2. 🤖 AI-Driven Insights (Powered by Gemini)
- **News Summarization**: Automatically aggregates and summarizes recent news, highlighting top stories.
- **Strategic Analysis**: Generates a "Core Strategic Focus" with Bull/Bear cases and Key Variances.
- **Financial Deep Dive**: Explains the "WHY" behind changes in Revenue, Profitability, and Cash Flow.
- **Segment Breakdown**: Extracts and visualizes revenue segments (e.g., AWS vs. North America) via AI.
- **Core Price Driver**: Identifies the single most important metric moving the stock right now.

### 3. ⚔️ Competitor Analysis
- **Dynamic Identification**: AI automatically identifies key competitors.
- **Comparison Table**: Side-by-side comparison of Price, P/E, Market Cap, and **Performance (3M, 6M, 1Y)**.
- **Relative Performance Chart**: Normalized 1-year return comparison.

## Tech Stack
- **Frontend**: Streamlit
- **Data**: yfinance, DuckDuckGo Search (news)
- **AI**: Google Gemini (via `google-generativeai`)
- **Visualization**: Plotly, Altair
- **Technical Analysis**: `ta` library (RSI, SMA)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd stock
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**:
   - Create a `.env` file in the root directory.
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

## Usage

Run the dashboard locally:
```bash
streamlit run app.py
```

## Project Structure
- `app.py`: Main Streamlit application and UI layout.
- `utils.py`: Core logic for data fetching, AI processing, and financial calculations.
- `.env`: Configuration file for API keys (not committed).

---
**Note**: This is a side project for educational and analytical purposes. Always do your own due diligence before investing.
