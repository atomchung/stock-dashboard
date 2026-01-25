"""
Sankey Structure Cache Manager

Manages persistent JSON storage for AI-inferred financial statement structures.
Once a ticker's structure is parsed by AI, it's cached to avoid repeated API calls.
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime

CACHE_FILE = "sankey_structures.json"


def load_cache() -> Dict:
    """Loads the entire cache from JSON file."""
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
        print(f"Error loading sankey cache: {e}")
        return {}


def get_cached_structure(ticker: str) -> Optional[Dict]:
    """
    Retrieves cached Sankey structure for a ticker.
    
    Returns:
        Dict with 'nodes' and 'links' if found, None otherwise
    """
    cache = load_cache()
    entry = cache.get(ticker.upper())
    if entry:
        return entry.get("structure")
    return None


def save_structure(ticker: str, structure: Dict) -> bool:
    """
    Saves AI-inferred Sankey structure to cache.
    
    Args:
        ticker: Stock ticker symbol
        structure: Dict with 'nodes' and 'links' keys
    
    Returns:
        True if saved successfully, False otherwise
    """
    cache = load_cache()
    
    cache[ticker.upper()] = {
        "structure": structure,
        "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"Sankey structure cached for {ticker}")
        return True
    except Exception as e:
        print(f"Error saving sankey cache: {e}")
        return False


def invalidate_cache(ticker: str) -> bool:
    """
    Removes cached structure for a ticker (for manual refresh).
    
    Returns:
        True if removed, False if not found or error
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
        print(f"Error invalidating sankey cache: {e}")
        return False
