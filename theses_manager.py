import json
import os
import uuid
from datetime import datetime

THESES_FILE = "theses.json"

def load_theses():
    """Lengths the existing theses from the JSON file."""
    if not os.path.exists(THESES_FILE):
        return []
    try:
        with open(THESES_FILE, "r") as f:
            content = f.read()
            if not content: return []
            return json.loads(content)
    except json.JSONDecodeError:
        print("JSON Decode Error in load_theses")
        return []
    except Exception as e:
        print(f"Error loading theses: {e}")
        # Return None to indicate failure, so we don't overwrite with empty
        return None

def save_thesis(thesis_data):
    """
    Saves a new thesis or updates an existing one.
    thesis_data should be a dict. If it has an 'id', it updates.
    Otherwise, it creates a new ID.
    """
    theses = load_theses()
    if theses is None: theses = [] # Fallback or handle error? 
    # Actually, if load fails, we risk overwriting. 
    # But for now, let's assume if it fails it's likely corrupt or locked.
    # Better to retry or fail. 
    
    # Simple fix: If it returns None, treat as empty list but log warning? 
    # Or strict: fail.
    # Given the user issue, the previous behavior was "Error -> [] -> Write []".
    # We should prevent writing if we suspect read error.
    if theses is None:
        return False, "Failed to load existing theses (File Access Error)."

    if "id" not in thesis_data or not thesis_data["id"]:
        thesis_data["id"] = str(uuid.uuid4())
        thesis_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_new = True
    else:
        is_new = False
        thesis_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update list
    if is_new:
        theses.append(thesis_data)
    else:
        found = False
        for i, t in enumerate(theses):
            if t["id"] == thesis_data["id"]:
                theses[i] = thesis_data
                found = True
                break
        if not found: theses.append(thesis_data) # recover if id exists but not found
    
    try:
        with open(THESES_FILE, "w") as f:
            json.dump(theses, f, indent=4)
        return True, thesis_data["id"]
    except Exception as e:
        return False, str(e)

def delete_thesis(thesis_id):
    """Deletes a thesis by ID."""
    theses = load_theses()
    if theses is None: return False # Protect against clearing file on load error
    
    original_len = len(theses)
    theses = [t for t in theses if t["id"] != thesis_id]
    
    if len(theses) == original_len:
        return False # ID not found?
    
    try:
        with open(THESES_FILE, "w") as f:
            json.dump(theses, f, indent=4)
        return True
    except Exception as e:
        return False

def get_empty_thesis_template(ticker=""):
    """Returns an empty thesis structure."""
    return {
        "id": "",
        "ticker": ticker,
        "thesis_statement": "",
        "falsification_condition": "",
        "confidence": 5,
        "time_horizon": "3-6 Months",
        "status": "Active" # Active, Verified, Falsified, Closed
    }
