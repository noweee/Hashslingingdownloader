import shutil
from pathlib import Path


def temp_dir(download_folder):
    return Path(download_folder) / "download" / "Temp"


def ensure_temp_dir(download_folder):
    path = temp_dir(download_folder)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_temp_dir(download_folder):
    path = temp_dir(download_folder)
    if path.exists():
        shutil.rmtree(path)


def clean_log_files(download_folder):
    base = Path(download_folder)
    removed = []
    if not base.exists():
        return removed
    for path in base.rglob("*log.txt"):
        try:
            if path.is_file():
                path.unlink()
                removed.append(path)
        except Exception:
            pass
    for path in base.glob("*.log"):
        try:
            if path.is_file():
                path.unlink()
                removed.append(path)
        except Exception:
            pass
    return removed


def clean_request_folders(download_folder):
    base = Path(download_folder) / "download"
    removed = []
    if not base.exists():
        return removed
    for path in base.iterdir():
        if path.name in {"Temp", ".gitkeep"}:
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
                removed.append(path)
            elif path.is_file():
                path.unlink()
                removed.append(path)
        except Exception:
            pass
    return removed


def clean_upload_registry(download_folder):
    path = Path(download_folder) / "upload_registry.json"
    if path.is_file():
        try:
            path.unlink()
            return True
        except Exception:
            return False
    return False
