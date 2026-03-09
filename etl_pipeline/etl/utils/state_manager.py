import json
from datetime import datetime
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state", "last_import.json")

def load_last_import_timestamp():
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_import_timestamp"].replace("Z", "+00:00"))
    except FileNotFoundError:
        return datetime(1970, 1, 1)

def save_last_import_timestamp(ts: datetime):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_import_timestamp": ts.isoformat()}, f)

