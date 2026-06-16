import json
from datetime import date
from pathlib import Path


COUNTERS_PATH = Path("daily_counters.json")


def _load():
    if not COUNTERS_PATH.is_file():
        return {"date": date.today().isoformat(), "users": {}}
    try:
        data = json.loads(COUNTERS_PATH.read_text())
    except json.JSONDecodeError:
        data = {"date": date.today().isoformat(), "users": {}}
    today = date.today().isoformat()
    if data.get("date") != today:
        return {"date": today, "users": {}}
    data.setdefault("users", {})
    return data


def get_count(user_id):
    data = _load()
    return int(data["users"].get(str(user_id), 0))


def ensure_available(user_id, tier):
    if tier.daily_cap is None:
        return
    used = get_count(user_id)
    if used >= tier.daily_cap:
        raise RuntimeError(f"Daily cap reached for {tier.label}: {used}/{tier.daily_cap}.")


def reserve(user_id, tier, amount=1):
    data = _load()
    key = str(user_id)
    used = int(data["users"].get(key, 0))
    if tier.daily_cap is not None and used + amount > tier.daily_cap:
        raise RuntimeError(f"Daily cap reached for {tier.label}: {used}/{tier.daily_cap}.")
    data["users"][key] = used + amount
    COUNTERS_PATH.write_text(json.dumps(data, indent=2))
    return data["users"][key]


def increment(user_id, amount=1):
    data = _load()
    key = str(user_id)
    data["users"][key] = int(data["users"].get(key, 0)) + amount
    COUNTERS_PATH.write_text(json.dumps(data, indent=2))
