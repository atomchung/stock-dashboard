"""
Earnings Calendar Cache Manager

Caches FMP earnings calendar results to minimize API calls.
Each ticker is only queried once per day.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime, date

CACHE_FILE = "earnings_cache.json"


def load_cache() -> Dict:
    """Loads the entire earnings cache from JSON file."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"Warning: JSONDecodeError in {CACHE_FILE}, returning empty cache")
        return {}
    except Exception as e:
        print(f"Error loading earnings cache: {e}")
        return {}


def get_cached_earnings(ticker: str) -> Optional[Dict]:
    """
    Retrieves cached earnings data for a ticker if it was cached today.
    
    Returns:
        Dict with earnings info if cached today, None if stale or not found
    """
    cache = load_cache()
    entry = cache.get(ticker.upper())
    
    if not entry:
        return None
    
    # Check if cached today
    cached_date = entry.get("cached_date")
    today = date.today().isoformat()
    
    if cached_date != today:
        print(f"[EarningsCache] Stale cache for {ticker} (cached: {cached_date}, today: {today})")
        return None
    
    print(f"[EarningsCache] Cache hit for {ticker}")
    return entry.get("data")


def save_earnings(ticker: str, data: Dict) -> bool:
    """
    Saves earnings data to cache with today's date.
    
    Args:
        ticker: Stock ticker symbol
        data: Dict with earnings info (next_earnings, dividend_date, etc.)
    
    Returns:
        True if saved successfully, False otherwise
    """
    cache = load_cache()
    
    cache[ticker.upper()] = {
        "data": data,
        "cached_date": date.today().isoformat(),
        "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"[EarningsCache] Cached earnings for {ticker}")
        return True
    except Exception as e:
        print(f"Error saving earnings cache: {e}")
        return False


def invalidate_cache(ticker: str) -> bool:
    """
    Removes cached earnings for a ticker (for manual refresh).
    """
    cache = load_cache()
    ticker_upper = ticker.upper()
    
    if ticker_upper not in cache:
        return False
    
    del cache[ticker_upper]
    
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        return True
    except Exception as e:
        print(f"Error invalidating earnings cache: {e}")
        return False
