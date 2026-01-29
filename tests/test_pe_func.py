
import pandas as pd
import yfinance as yf
# Mock streamlit session state to avoid import errors if utils uses it? 
# utils.py seems independent of streamlit.
from obb_utils import get_pe_band_data

symbol = "CAVA"
print(f"Testing get_pe_band_data for {symbol}...")
df = get_pe_band_data(symbol)

if df.empty:
    print("Result DF is EMPTY")
else:
    print(f"Result DF Shape: {df.shape}")
    print("Columns:", df.columns)
    print("First 5 rows:")
    print(df.head())
    print("Last 5 rows:")
    print(df.tail())
    
    # Check for NaNs
    print("NaN counts:")
    print(df.isna().sum())
