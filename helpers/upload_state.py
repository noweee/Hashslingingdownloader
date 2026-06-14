import json
from pathlib import Path


STATE_PATH = Path("last_upload.json")


def get_last_upload():
    if not STATE_PATH.is_file():
        return None
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return None


def set_last_upload(remote_file, display_name):
    STATE_PATH.write_text(json.dumps({"remote_file": remote_file, "display_name": display_name}, indent=2))
