import json
import time
from pathlib import Path


REGISTRY_PATH = Path("upload_registry.json")


def _load():
    if not REGISTRY_PATH.is_file():
        return []
    try:
        data = json.loads(REGISTRY_PATH.read_text())
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _save(items):
    REGISTRY_PATH.write_text(json.dumps(items, indent=2))


def add_upload(remote_file, display_name, user_id, channel_id):
    items = _load()
    items.append(
        {
            "remote_file": remote_file,
            "display_name": display_name,
            "user_id": user_id,
            "channel_id": channel_id,
            "created_at": time.time(),
        }
    )
    _save(items)


def remove_upload(remote_file):
    _save([item for item in _load() if item.get("remote_file") != remote_file])


def oldest_upload():
    items = [item for item in _load() if item.get("remote_file")]
    if not items:
        return None
    return sorted(items, key=lambda item: item.get("created_at", 0))[0]


def uploads_for_user(user_id):
    return [item for item in _load() if item.get("user_id") == user_id and item.get("remote_file")]


def remove_uploads_for_user(user_id):
    items = _load()
    kept = [item for item in items if item.get("user_id") != user_id]
    removed = [item for item in items if item.get("user_id") == user_id and item.get("remote_file")]
    _save(kept)
    return removed
