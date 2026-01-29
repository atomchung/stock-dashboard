
import json
import logging
from typing import Dict, List, Optional, Any, TypedDict, Union
import os
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Types ---

class NewsItem(TypedDict):
    title: str
    url: str
    source: str
    date: str
    body: str

class MarketContext(TypedDict):
    ticker: str
    news: List[NewsItem]
    earnings_context: List[Any] # Raw DDG results for earnings
    financial_context: List[Any] # Raw DDG results for financials
    events_context: List[Any] # Raw DDG results for events
    
# --- Base Prompts & Helpers ---

BASE_INSTRUCTIONS = """
You are an expert Financial Analyst and Investment Strategist.
Your goal is to provide accurate, balanced, and actionable insights based on the provided context.

**Formatting Rules (Strict Application)**:
- **NO LaTeX**: Do NOT use LaTeX formatting (e.g., $...$, \\frac). It breaks the frontend renderer.
- **Currency**: Format currency strictly as "$10.5 billion" or "10.5 billion USD". Do NOT use "$10.5B$" or "$10.5 billion$".
- **Markdown**: Use standard Markdown (bold, lists, headers).
- **Objectivity**: distinguish between fact and analyst opinion.
- **No Hallucinations**: Only use the provided context. if information is missing, state it.
"""

def clean_json_text(text: str) -> str:
    """Cleans code fencing from llm output to ensure json.loads works."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# --- StockAgent Class ---

class StockAgent:
    # Valid Models for REST API
    # User requested Gemini 3.0 Flash. Using the preview versions available in the API list.
    MODEL_PRO = 'gemini-3-flash-preview' # Using Flash for speed as requested, or 'gemini-3-pro-preview'
    MODEL_FLASH = 'gemini-3-flash-preview'
    
    def __init__(self, api_key: str, ticker: str):
        self.api_key = api_key
        self.ticker = ticker
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _generate(self, prompt: str, use_json: bool = False, use_pro: bool = False) -> str:
        """
        Internal helper to call Gemini REST API with error handling and timeout.
        """
        if not self.api_key:
            return "Error: API Key missing."

        model_name = self.MODEL_PRO if use_pro else self.MODEL_FLASH
        url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add base instructions
        full_prompt = f"{BASE_INSTRUCTIONS}\n\n{prompt}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        if use_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            # Enforce 30 second timeout to prevent hanging (increased from 15s)
            logger.debug(f"Calling Gemini REST API ({model_name})...")
            response = requests.post(url, headers=headers, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                logger.error(f"Gemini API Error {response.status_code}: {response.text}")
                return f"Error: API returned {response.status_code}"
                
            data = response.json()
            # Extract text from response
            try:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text
            except (KeyError, IndexError):
                logger.error(f"Unexpected API response format: {data}")
                return "Error: Malformed API response"
                
        except requests.exceptions.Timeout:
            logger.error(f"Gemini API Timeout (30s)")
            return "Error: Request Timed Out"
        except Exception as e:
            logger.error(f"Gemini Generation Error ({model_name}): {e}")
            return f"Error analyzing data: {str(e)}"

    def check_api_key(self) -> bool:
        return bool(self.api_key)

    # --- Feature Methods ---

    def analyze_news(self, news_items: List[Dict]) -> str:
        """Summarizes news and lists top reading choices."""
        if not self.check_api_key(): return "Please provide a gemini API Key to see the summary."
        
        # Prepare context
        news_text = ""
        for i, item in enumerate(news_items[:10]):
            news_text += f"{i+1}. {item.get('title')} ({item.get('source')}) - {item.get('body')}\n"
            
        prompt = f"""
        **Task**: Summarize recent news for {self.ticker} and identify top articles.
        
        **News Context**:
        {news_text}
        
        **Output Requirements**:
        1. **Executive Summary**: A concise paragraph explaining the current sentiment and main drivers.
        2. **Top 3 Articles**: List the 3 most important articles.
           Format: `• **[Title]**: Why it's important.`
           
        **Constraint**: Focus ONLY on {self.ticker}. Ignore generic market news unless directly relevant.
        """
        return self._generate(prompt, use_pro=False)  # Flash: simple summarization

    def analyze_strategy(self, context_results: List[Dict], news_context: Optional[List[Dict]] = None, company_info: Optional[Dict] = None) -> str:
        """Generates Bull/Bear case analysis with structured, evidence-based output and news consistency check."""
        if not self.check_api_key(): return "Please provide a gemini API Key."
        if not context_results: return "No details found for strategy analysis."

        # Build context text with source attribution
        context_text = "\n".join([
            f"- [{item.get('source', 'Unknown')}] {item.get('title', '')}: {item.get('body', '')}"
            for item in context_results
        ])
        
        # Build News Context for Cross-Check
        news_text = ""
        if news_context:
            news_text = "\n".join([
                f"- {item.get('date', '')} {item.get('title', '')}: {item.get('body', '')[:200]}"
                for item in news_context[:5] # Check top 5 recent news
            ])
        
        # Get current date for time context
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Extract company background if available
        company_name = company_info.get('shortName', self.ticker) if company_info else self.ticker
        sector = company_info.get('sector', 'Unknown') if company_info else 'Unknown'
        business = company_info.get('longBusinessSummary', '')[:500] if company_info else ''
        
        prompt = f"""
**Task**: Synthesize a Strategic Bull/Bear Analysis for {self.ticker} ({company_name}).

**Current Date**: {current_date}
**Sector**: {sector}
**Business**: {business if business else 'See context for business details.'}

**Context (Deep Analysis/Earnings)**:
{context_text[:12000]}

**Recent News (For Consistency Check)**:
{news_text if news_text else "No recent news available."}

---

**step-by-step reasoning**:
1. Analyze the "Deep Analysis" context to build the core Bull/Bear arguments.
2. Cross-reference with "Recent News". Does any recent event (last 7 days) CONTRADICT the deep analysis indicators?
   - Example: Deep analysis says "Strong Growth", but News says "CEO Fired for Fraud yesterday".
   - If yes, you MUST include a warning.

---

**OUTPUT REQUIREMENTS** (Follow this structure exactly):

### ⚠️ CRITICAL NEWS ALERT (Optional)
**Only** include this section if Recent News significantly invalidates the Deep Analysis (e.g., bankruptcy, fraud, massive recall).
Format: "**[Date] [Event]**: This recent event may invalidate the [Bull/Bear] thesis below because..."

### 🐂 Bull Case
Provide a narrative with MANDATORY elements:
1. **Revenue/Growth**: Cite a specific growth metric (e.g., "Revenue grew X% YoY in QX 20XX")
2. **Margin/Profitability**: Mention margin trend with numbers if available
3. **Catalyst**: Identify ONE specific upcoming event with approximate date
4. **Competitive Position**: Name a specific advantage or market position

### 🐻 Bear Case
Provide a narrative with MANDATORY elements:
1. **Financial Risk**: Cite ONE concerning metric (debt, cash burn, concentration)
2. **Execution Challenge**: Identify ONE specific operational risk
3. **Competitive Threat**: Name specific competitors or market pressures
4. **Valuation/Timing Risk**: Address if current price reflects optimistic assumptions

### 🔑 Key Variance
Format: "The core debate is whether [specific metric/event] will [specific outcome] by [timeframe]."

---

**CRITICAL RULES**:
1. If data for any required element is NOT in the context, write: "[DATA NOT FOUND: element name]"
2. Do NOT use vague phrases like:
   - "potential challenges"
   - "may face risks"  
   - "could grow"
   - "further research would be needed"
   - "unidentified risks"
3. Every claim MUST have a number, date, or named entity attached
4. Reference specific quarters (Q1 2025, Q4 2024) not vague timeframes
5. Cite sources where possible (e.g., "According to SeekingAlpha...")

**Style**: Professional narrative. Lead with the strongest evidence.
"""
        return self._generate(prompt, use_pro=True)  # Pro: complex multi-factor reasoning

    def analyze_strategic_intelligence(self, context_results: List[Dict], news_context: Optional[List[Dict]] = None, company_info: Optional[Dict] = None) -> str:
        """
        Combines Executive Pulse (News) and Strategic Thesis (Bull/Bear) into a coherent intelligence report.
        """
        if not self.check_api_key(): return "Please provide a gemini API Key."
        
        # Build context text with source attribution
        context_text = "\n".join([
            f"- [{item.get('source', 'Unknown')}] {item.get('title', '')}: {item.get('body', '')}"
            for item in context_results
        ])
        
        # Build News Context
        news_text = "No recent news available."
        if news_context:
            news_text = "\n".join([
                f"- {item.get('date', '')} {item.get('title', '')}: {item.get('body', '')[:200]}"
                for item in news_context[:8]
            ])
        
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        company_name = company_info.get('shortName', self.ticker) if company_info else self.ticker
        sector = company_info.get('sector', 'Unknown') if company_info else 'Unknown'
        
        prompt = f"""
**Task**: Generate a Strategic Intelligence Report for {self.ticker} ({company_name}).
**Date**: {current_date}
**Sector**: {sector}

**Goal**: Merge short-term market sentiment with long-term strategic analysis. ensure coherence between news and thesis.

**Input 1: Deep Strategic Context (Earnings/Analyst Reports)**:
{context_text[:12000]}

**Input 2: Recent Market News (Last 7 Days)**:
{news_text}

---

**OUTPUT SECTIONS** (Use Markdown):

### 📡 Market Pulse (Executive Summary)
- **Sentiment**: 1 sentence on the immediate mood (Bullish/Bearish/Neutral).
- **Top Catalyst**: 1-2 sentences on the single most critical news item or event driving price right now.
- *Constraint*: Be extremely concise. Do not list articles.

### 🛡️ Strategic Thesis (Bull/Bear)
*Synthesis of long-term fundamentals.*

**🐂 Bull Case**
- **Growth Engine**: specific metric/product driving upside (cite numbers).
- **Margin Story**: profitability trend.
- **Moat**: competitive advantage or unique positioning.

**🐻 Bear Case**
- **Core Risk**: specific financial or operational danger (cite numbers).
- **Competition**: threat from specific rival.
- **Valuation**: is it priced for perfection?

**🔑 Key Variance**
- The one critical debate that will determine the stock's future (e.g. "Can AI revenue grow fast enough to justify 50x PE?").

---
**Rules**:
1. If news contradicts strategy (e.g. "Strong Growth" thesis but "CEO Fired" news), highlight the conflict in the Market Pulse.
2. Use specific numbers and dates.
3. No fluff.
"""
        return self._generate(prompt, use_pro=True)

    def analyze_events(self, context_results: List[Dict], confirmed_dates: Optional[Dict] = None) -> str:
        """Generates Past/Future event timeline with API-confirmed dates."""
        if not self.check_api_key(): return "No API Key."
        
        context_text = "\n".join([f"- {item.get('title')} ({item.get('date', '')}): {item.get('body')}" for item in context_results])

        # Format confirmed dates
        dates_text = ""
        if confirmed_dates:
            if confirmed_dates.get('next_earnings'):
                 dates_text += f"- **CONFIRMED NEXT EARNINGS**: {confirmed_dates['next_earnings']}\n"
            if confirmed_dates.get('dividend_date'):
                 dates_text += f"- **DIVIDEND DATE**: {confirmed_dates['dividend_date']}\n"
            if confirmed_dates.get('ex_dividend'):
                 dates_text += f"- **EX-DIVIDEND**: {confirmed_dates['ex_dividend']}\n"

        prompt = f"""
        **Task**: Identify Major Corporate Events for {self.ticker}.
        
        **API-Confirmed Dates (PRIORITIZE THESE for "Upcoming Catalysts")**:
        {dates_text if dates_text else "No confirmed API dates found."}
        
        **Context (Use for past events and unofficial future events)**:
        {context_text}
        
        **Output Requirements**:
        - **🕒 Recent Highlights (Past 3 Months)**: List completion dates and events.
        - **🔮 Upcoming Catalysts (Next 3 Months)**: 
            - **MANDATORY**: You MUST include the 'CONFIRMED NEXT EARNINGS' date from above if available.
            - List other product launches, FDA approvals etc.
        
        Format as clear bullet points. If no upcoming events, explicitly state it.
        """
        return self._generate(prompt, use_pro=False)  # Flash: structured extraction

    def analyze_financials(self, context_results: List[Dict]) -> str:
        """Explains WHY financial metrics changed."""
        if not self.check_api_key(): return "No API Key."
        if not context_results: return "No financial analysis found."

        context_text = "\n".join([f"- {item.get('body')}" for item in context_results])
        
        prompt = f"""
        **Task**: Explain the drivers behind {self.ticker}'s recent financial performance.
        
        **Context**:
        {context_text}
        
        **Output Sections**:
        1. **Revenue Drivers**: What segments/products grew or declined?
        2. **Profitability**: Margins, efficiency, or cost issues.
        3. **Cash & Capital**: Specifics on buybacks, debt, or Capex if mentioned.
        
        **Constraint**: Be specific. Use numbers from text (e.g. "Cloud grew 20%").
        """
        return self._generate(prompt, use_pro=True)  # Pro: financial reasoning

    def extract_revenue_segments(self, context_results: List[Dict]) -> str:
        """Extracts revenue segments as JSON."""
        if not self.check_api_key(): return "[]"
        if not context_results: return "[]"

        context_text = "\n".join([f"- {item.get('body')}" for item in context_results])
        
        prompt = f"""
        **Task**: Extract the most recent Revenue Breakdown by Segment for {self.ticker}.
        
        **Context**:
        {context_text}
        
        **Output**: JSON Array ONLY. 
        Example: `[{{"label": "Cloud", "value": 25.5, "growth": "+10%"}}]`
        - `value`: Number (Billions USD preferred).
        - `growth`: String (e.g. "+12%").
        """
        
        res = self._generate(prompt, use_json=True, use_pro=False)  # Flash: JSON extraction
        return clean_json_text(res)

    def identify_core_driver(self, context_results: List[Dict]) -> str:
        """Identifies #1 price driver."""
        if not self.check_api_key(): return "N/A"
        
        context_text = "\n".join([f"- {item.get('title')}: {item.get('body')}" for item in context_results[:5]])
        
        prompt = f"""
        Based on the news for {self.ticker}:
        What is the single #1 specific metric or narrative driver moving the stock?
        Return ONLY the driver name (Max 5 words). No punctuation.
        
        Context: {context_text}
        """
        return self._generate(prompt, use_pro=True).strip()  # Pro: requires synthesis

    def identify_competitors(self) -> List[str]:
        """Identifies top competitors or industry peers."""
        if not self.check_api_key(): return []
        
        prompt = f"""
        Identify the top 4 public company competitors or industry peers for {self.ticker}.
        
        IMPORTANT RULES:
        1. Focus on companies in the SAME industry/sector with similar business models
        2. Prefer companies with similar market cap size (small-cap with small-cap, large-cap with large-cap)
        3. If no direct competitors exist, list companies in the same industry that investors would compare against
        4. ONLY include publicly traded US stocks with valid ticker symbols
        5. If you truly cannot find any relevant peers, return an empty list []
        
        DO NOT list unrelated mega-cap tech stocks (AAPL, MSFT, GOOG, AMZN) unless they are actual direct competitors.
        
        Return ONLY a valid JSON list of ticker symbols.
        Example: ["TICKER1", "TICKER2", "TICKER3", "TICKER4"]
        """
        res = self._generate(prompt, use_json=True, use_pro=False)  # Flash: knowledge lookup
        try:
            result = json.loads(clean_json_text(res))
            # Validate result is a list of strings
            if isinstance(result, list) and all(isinstance(t, str) for t in result):
                return result[:4]  # Limit to 4
            return []
        except:
            return []

    def get_branding_keywords(self) -> List[str]:
        """Identifies branding keywords."""
        if not self.check_api_key(): return []
        
        prompt = f"""
        Identify for {self.ticker}:
        1. Parent Company Name
        2. Famous Product Names (Top 3)
        3. Alternative Tickers
        
        Return ONLY a comma-separated list of keywords.
        """
        res = self._generate(prompt, use_pro=False)  # Flash: simple knowledge lookup
        return [k.strip() for k in res.split(',') if k.strip()]

    def generate_thesis(self, context_text: str, user_keywords: str = "") -> Dict:
        """Generates a falsifiable investment thesis."""
        if not self.check_api_key(): return {"error": "No API Key"}
        
        prompt = f"""
        **Task**: Generate a Falsifiable Investment Thesis for {self.ticker}.
        
        **Context**:
        {context_text[:10000]}
        
        **User Focus**: {user_keywords}
        
        **Philosophy**: Karl Popper's Falsifiability. A thesis must have a clear "Kill Switch" (condition that proves it wrong).
        
        **Output JSON**:
        {{
            "thesis_statement": "The core argument...",
            "falsification_condition": "Specific, measurable event/metric...",
            "time_horizon": "3-6 Months",
            "confidence": 7
        }}
        """
        res = self._generate(prompt, use_json=True, use_pro=True)  # Pro: thesis generation
        try:
            return json.loads(clean_json_text(res))
        except Exception as e:
            return {"error": f"Failed to parse thesis: {e}"}

    def refine_thesis(self, current_thesis: Dict, instruction: str) -> Dict:
        """Refines thesis based on user instruction."""
        if not self.check_api_key(): return current_thesis
        
        prompt = f"""
        **Task**: Refine this investment thesis based on feedback.
        
        **Current Thesis**:
        Statement: {current_thesis.get('thesis_statement')}
        Kill Switch: {current_thesis.get('falsification_condition')}
        
        **Feedback**: "{instruction}"
        
        **Output JSON**:
        Return the full JSON object with updated fields.
        """
        res = self._generate(prompt, use_json=True, use_pro=True)  # Pro: thesis refinement
        try:
            return json.loads(clean_json_text(res))
        except:
            return current_thesis

    def infer_sankey_structure(self, income_stmt_data: Dict) -> Optional[Dict]:
        """
        Uses AI to dynamically analyze income statement and return Sankey structure.
        
        Args:
            income_stmt_data: Dict of field names to values from income statement
            
        Returns:
            Dict with 'nodes' and 'links' keys, or None on failure
        """
        if not self.check_api_key():
            return None
        
        # Filter out NaN/None values for cleaner prompt
        clean_data = {k: v for k, v in income_stmt_data.items() 
                      if v is not None and str(v) != 'nan' and v != 0}
        
        prompt = f"""
**Task**: Analyze this Income Statement data for {self.ticker} and create a Sankey diagram structure.

**Raw Financial Data**:
```json
{json.dumps(clean_data, indent=2, default=str)}
```

**Output Requirements**:
Return a JSON object with this exact structure:
{{
    "nodes": [
        {{"name": "Total Revenue", "layer": 0}},
        {{"name": "Cost of Revenue", "layer": 1}},
        {{"name": "Gross Profit", "layer": 1}},
        ...
    ],
    "links": [
        {{"source": "Total Revenue", "target": "Cost of Revenue", "field": "Cost Of Revenue"}},
        {{"source": "Total Revenue", "target": "Gross Profit", "field": "Gross Profit"}},
        ...
    ],
    "field_mapping": {{
        "Total Revenue": "Total Revenue",
        "Cost of Revenue": "Cost Of Revenue",
        ...
    }}
}}

**RULES**:
1. **layers**: 0=Revenue sources, 1=First split (GP/COGS), 2=OpEx breakdown, 3=Final (Net Income)
2. **field_mapping**: Maps display name to actual field name in the data
3. **Conservation**: Sum of outflows from each node should roughly equal the node value
4. **Only use fields that exist in the data** - check field names exactly
5. For banks: Use Interest Income/Expense structure instead of traditional COGS
6. For insurance: Use Premium Income structure
7. Keep it simple: Maximum 10 nodes total
8. **links.field**: The actual field name to fetch value from

**Common field name patterns to look for**:
- Revenue: "Total Revenue", "Revenue", "Net Sales"
- Costs: "Cost Of Revenue", "Cost of Goods Sold"
- Profit: "Gross Profit", "Operating Income", "Net Income"
- Expenses: "Research And Development", "Selling General And Administration", "Operating Expense"
- Tax: "Tax Provision", "Income Tax Expense"
- Banks: "Interest Income", "Interest Expense", "Net Interest Income"

Return ONLY valid JSON, no markdown fencing.
"""
        
        res = self._generate(prompt, use_json=True, use_pro=False)  # Flash: structured JSON
        try:
            structure = json.loads(clean_json_text(res))
            # Validate structure
            if 'nodes' in structure and 'links' in structure:
                logger.info(f"Successfully inferred Sankey structure for {self.ticker}")
                return structure
            else:
                logger.warning(f"Invalid Sankey structure returned for {self.ticker}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Sankey structure JSON: {e}")
            return None

