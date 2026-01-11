# Changelog

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
