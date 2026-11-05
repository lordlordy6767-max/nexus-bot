import json
import os
DATA_DIR = os.environ.get("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

FILE = os.path.join(DATA_DIR, "balances.json")
_balances = {}
_daily_claimed = {}

if os.path.exists(FILE):
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
            _balances = {int(k): int(v) for k, v in data.get("balances", {}).items()}
            _daily_claimed = {int(k): float(v) for k, v in data.get("daily", {}).items()}
    except Exception:
        _balances = {}
        _daily_claimed = {}

def _save():
    try:
        with open(FILE, "w") as f:
            json.dump({"balances": _balances, "daily": _daily_claimed}, f)
    except Exception as e:
        print(f"WALLET SAVE ERROR: {e}")

def get_bal(user_id: int) -> int:
    return _balances.get(int(user_id), 0)

def add(user_id: int, amount: int) -> int:
    user_id = int(user_id)
    _balances[user_id] = get_bal(user_id) + int(amount)
    _save()
    return _balances[user_id]

def get_daily_last(user_id: int) -> float:
    return _daily_claimed.get(int(user_id), 0)

def set_daily(user_id: int, now: float):
    _daily_claimed[int(user_id)] = now
    _save()