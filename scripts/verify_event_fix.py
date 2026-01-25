import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils
import json

def verify():
    ticker = "ONDS"
    print(f"--- Verifying Hybrid Search for {ticker} ---")
    
    # 1. Test Search Logic Directly
    try:
        print("Fetching results via utils.search_key_events...")
        results = utils.search_key_events(ticker)
        print(f"Total Results: {len(results)}")
        
        found_earnings_keyword = False
        for i, res in enumerate(results):
            title = res.get('title', '')
            snippet = res.get('body', '')
            source = res.get('source', 'Web')
            print(f"[{i+1}] {title} ({source})")
            
            # Check for earnings keywords
            if "earnings" in title.lower() or "earnings" in snippet.lower():
                found_earnings_keyword = True
                
        if found_earnings_keyword:
            print("\n✅ SUCCESS: 'Earnings' related content found in results.")
        else:
            print("\n❌ WARNING: No direct 'Earnings' keyword found in snippets.")
            
    except Exception as e:
        print(f"❌ Error during search verification: {e}")

if __name__ == "__main__":
    verify()
