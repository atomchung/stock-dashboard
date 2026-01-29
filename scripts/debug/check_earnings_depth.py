
import yfinance as yf
t = yf.Ticker("NVDA")
print("--- Earnings Dates ---")
try:
    # earnings_dates usually has a long history of reported EPS
    ed = t.earnings_dates
    print(ed.head())
    print(ed.tail())
    print("Columns:", ed.columns)
    print("Length:", len(ed))
except Exception as e:
    print(e)
