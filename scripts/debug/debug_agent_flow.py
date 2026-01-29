
import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from agent import StockAgent
import utils
import time

def debug_agent():
    api_key = os.getenv("GEMINI_API_KEY")
    ticker = "CAVA"
    print(f"--- Testing Agent for {ticker} ---")
    
    agent = StockAgent(api_key, ticker)
    
    # Real data for extract_revenue_segments
    print(f"Searching DDG for segments...")
    real_context = utils.search_revenue_segments(ticker)
    print(f"Found {len(real_context)} results.")
    
    print("Calling extract_revenue_segments with REAL data...")
    start = time.time()
    try:
        res = agent.extract_revenue_segments(real_context)
        print(f"Result: {res}")
        print(f"Time: {time.time() - start:.2f}s")
    except Exception as e:
        print(f"CRASH: {e}")

if __name__ == "__main__":
    debug_agent()
