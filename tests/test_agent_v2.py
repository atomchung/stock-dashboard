import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import StockAgent
import json

def test_agent_structure():
    print("Testing StockAgent Structure...")
    agent = StockAgent(api_key="test_key", ticker="TEST")
    
    assert agent.ticker == "TEST"
    assert agent.api_key == "test_key"
    print("Initialize OK.")
    
    # Test method existence
    methods = [
        "analyze_news", "analyze_strategy", "analyze_events", 
        "analyze_financials", "extract_revenue_segments", 
        "identify_core_driver", "identify_competitors", 
        "get_branding_keywords", "generate_thesis", "refine_thesis",
        "_generate_stream"
    ]
    
    for m in methods:
        if not hasattr(agent, m):
            print(f"FAILED: Missing method {m}")
        else:
            print(f"Method {m} exists.")

    print("Structure Check passed.")

def test_missing_key():
    print("\nTesting Missing Key Handling...")
    agent = StockAgent(api_key="", ticker="TEST")
    
    res = agent.analyze_news([{"title": "foo"}])
    if "Please provide a gemini API Key" in res or "No API Key" in res:
        print("Graceful failure OK.")
    else:
        print(f"FAILED: Expected error message, got '{res}'")

if __name__ == "__main__":
    test_agent_structure()
    test_missing_key()
