# Changelog

## v0.6.4 (2025-01-11) - AI Logic Precision (GOOG Repair)
- **Refined**: AI News Summary prompt now explicitly bans hallucinating connections to competitors (e.g. fixing NVDA news appearing for GOOG).
- **Refined**: Polymarket filtering is now fully dynamic. AI now identifies "Sibling Tickers" (GOOG/GOOGL) and "Colloquial Names" (Google/Alphabet) to filter markets, replacing hardcoded aliases.

## v0.6.3 (2025-01-11) - Fixes (GOOG & Caching)
- **Fix**: Implemented session state clearing when switching tickers, resolving the "Sticky News" bug (e.g. showing NVDA news for GOOG).
- **Fix**: Added manual aliasing for dual-class stocks (GOOG/GOOGL) to ensure Polymarket results appear regardless of which ticker is searched.

## v0.6.2 (2025-01-11) - Polymarket Precision
- **Feature**: Added AI-powered relevancy filtering for Prediction Markets.
- **Logic**: Markets are now filtered to ensure they mention the Company, Ticker, or **top famous products** (identified by Gemini, e.g. "iPhone" for AAPL).

## v0.6.1 (2025-01-11) - Polymarket Robustness
- **Fix**: Resolved "No markets found" for tickers like AAPL by adding a fallback search for Company Name (e.g. "Apple").
- **Fix**: Removed invalid API sort parameters causing 422 errors; moved sorting to client-side.

## v0.6 (2025-01-11) - Market Sentiment (Polymarket)
- **Feature**: Integrated Polymarket API to display top 5 betting markets related to the ticker.
- **UI**: Added "Prediction Markets" section in News tab showing Volume and Odds.

## v0.5 (2025-01-11) - Formatting Patch
- **Fixed**: Eliminated "missing spaces" bug (e.g. `27.5billion`) by strictly forbidding AI from using LaTeX math mode (`$...$`) for emphasis.
- **Refined**: AI prompts now explicitly instruct proper currency formatting (e.g. "$27.5 billion").
- **Docs**: Added `DEVELOPMENT_RULES.md` to track coding standards.

## v0.4 (2025-01-11) - Fixes & Content Polish
- **Fix**: Restored "Latest Articles" section (found missing) and added robust fallback text.
- **Content**: Cleaned up AI text generation to prevent missing spaces (e.g., "The300Billion") and detached asterisks (`**`).
- **Refinement**: Simplified AI prompts for cleaner headers and lists.

## v0.3 (2025-01-11) - Quality & Precision
- **Visuals**: Charts now show BOTH comma-formatted values and QoQ growth % (restored).
- **Sankey**: Optimized layout (`snap`) to reduce node crossing/blocking.
- **Data Freshness**: Search queries now enforced to "Past Year" (`timelimit='y'`) to filter out outdated news.
- **AI Content**:
    - **Strategy**: Refined prompt for smoother narrative flow (less forced numbers).
    - **Financials**: Instructed AI to extract specific facts (Amounts, Rates, Prices) for financing events.

## v0.2 (2025-01-11) - Timeline Upgrade
- **Future Events**: News Timeline now searches for BOTH "Recent" (Past 3 months) and "Upcoming" (Next 3 months) catalysts.

## v0.1 (2025-01-11) - Robustness & Insights
- **Robustness**: Fixed chart crashes caused by non-numeric financial data. Charts now gracefully skip missing metrics.
- **Deep Strategy**: "Bull vs Bear" analysis now explicitly cites financial KPIs and metrics.
- **Key Events**: Added a "Recent Major Events" timeline (3 months) to the News tab.

## v0 (2025-01-11)
- **Initial Release**: Basic dashboard with Stock Data, AI News, and Financials.
- **Sankey Diagram**: Visualized Income Statement flow. Added specific quarter labeling (e.g., 25Q3) and optimized layout.
- **Competitor Analysis**: Added AI-driven competitor detection and 3M/6M/1Y performance comparison.
- **Charts**: Added Gross Profit chart and formatted numbers to `1,000.1` style.
- **Infrastructure**: GitHub integration and local environment setup.
