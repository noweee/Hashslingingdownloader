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
