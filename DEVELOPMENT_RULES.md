# Development Guidelines & Best Practices

This document serves as a living record of development standards and "lessons learned" to prevent recurring issues. BEFORE making changes, cross-reference this list.

## 1. 🛡️ Data Robustness & Error Handling
**Goal**: The application must NEVER crash due to missing, malformed, or unexpected external data.

*   **Handling Missing Metrics**:
    *   **Always** check if data exists before plotting.
    *   **Rule**: If a metric (e.g., "Gross Profit") is missing from the dataframe, explicitly handle it (e.g., set to `0` or `pd.Series([0])`) or skip the chart entirely with a user-friendly "Data Unavailable" message.
    *   **Anti-Pattern**: Accessing `df.loc['Metric']` without checking `if 'Metric' in df.index`.

*   **Data Type Safety**:
    *   **Always** force numeric conversion before mathematical operations or plotting.
    *   **Code**: `pd.to_numeric(series, errors='coerce').fillna(0)`
    *   **Why**: APIs may return strings ("100M") or `None` mixed with floats.

*   **Search & Data Freshness**:
    *   **Always** enforce time limits on search queries to avoid outdated context.
    *   **Code**: `DDGS().news(keywords=..., timelimit="y")` (Past Year).
    *   **Why**: Without this, news searches often return results from 1-2 years ago.

## 2. 🧠 AI Prompt Engineering
**Goal**: AI outputs must be precise, readable, and factually grounded.

*   **Formatting Rigor**:
    *   **Explicitly Forbidden**: Random/detached asterisks (`**` in the middle of sentences).
    *   **Spacing**: Explicitly instruct the model to "Ensure proper spacing between words" (prevents "The300Billion" issues).
    *   **Style**: "Smooth narrative flow" > "Forced number insertion".
    *   **LaTeX Ban**: **Do NOT use LaTeX math mode ($...$)**. Streamlit renders this by removing spaces. Usage of `$` must *only* be for currency (e.g., "$50M"), never closing with another `$`.

*   **Specificity & Factuality**:
    *   **Rule**: Do not ask generic questions ("How is the financial health?").
    *   **Requirement**: Ask for specific data points: "What specific amounts ($M) were raised? At what interest rate? With which counterparty?".
    *   **Fallback**: If no events/facts are found, the AI must explicitly state "No major events found" rather than hallucinating vague text.

## 3. 📊 UI/UX & Visualization Standards
**Goal**: Dashboard should be compact, information-dense, and aesthetically clean.

*   **Sankey Diagrams**:
    *   **Layout**: Always use `arrangement='snap'` in Plotly Sankey traces.
    *   **Why**: Prevents nodes from overlapping/tangling, ensuring a clean flow.
    *   **Labels**: Include specific timeframes (e.g., "25Q3") in titles.

*   **Charts**:
    *   **Density**: Prefer "Compact" bar charts with data labels *on* or *above* the bars.
    *   **Context**: Display **Growth %** (QoQ/YoY) alongside the absolute value (e.g., `$1,000M (+5.2%)`).
    *   **Axes**: Use `format_large_number` (1.2B, 900M) for readability.

*   **Section Visibility**:
    *   **Fallback Content**: *Never* leave a section blank if data is missing.
    *   **Rule**: `if data: show_data() else: st.write("No data found")`.
    *   **Why**: Users assume the app is broken if a section header appears with no content.

## 4. 🛠️ Workflow & Code Quality
*   **Change Management**:
    *   **Changelog**: Update `CHANGELOG.md` with every significant iteration (v0.1, v0.2, etc.).
    *   **Task List**: Maintain a `task.md` to track iterations and "Done" state.

*   **Testing**:
    *   **Validation**: After any logic change, verify manually against a "Corner Case" stock (e.g., one with no revenue, or no news) to test robustness.
    *   **Format Check**: Visually inspect AI text output for "Markdown Breakage".
