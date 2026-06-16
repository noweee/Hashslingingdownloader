from pathlib import Path
import shutil
from uuid import uuid4


def create_request_context(base_folder):
    request_id = uuid4().hex[:10]
    temp_path = Path(base_folder) / "download" / request_id
    temp_path.mkdir(parents=True, exist_ok=True)
    return request_id, temp_path


def cleanup_request_context(temp_path):
    temp_path = Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)
    shutil.rmtree(temp_path.parent / ".streamrip_appdata" / temp_path.name, ignore_errors=True)
