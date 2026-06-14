import re
import zipfile
from pathlib import Path
import asyncio


IGNORED_NAMES = {".spotdl-cache"}


def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "download"


def downloadable_entries(temp_path):
    temp_path = Path(temp_path)
    return [
        entry
        for entry in temp_path.iterdir()
        if entry.name not in IGNORED_NAMES and not entry.name.lower().endswith(".zip")
    ]


def artifact_name_from_temp(temp_path, fallback="download"):
    entries = downloadable_entries(temp_path)
    if not entries:
        raise RuntimeError("Downloader finished but did not create any files.")
    if len(entries) == 1:
        entry = entries[0]
        return safe_filename(entry.stem if entry.is_file() else entry.name)
    return safe_filename(fallback or "playlist")


def make_zip_from_temp(temp_path, archive_name=None):
    temp_path = Path(temp_path)
    archive_name = safe_filename(archive_name or artifact_name_from_temp(temp_path))
    zip_path = temp_path / f"{archive_name}.zip"

    entries = downloadable_entries(temp_path)
    if not entries:
        raise RuntimeError("No downloaded files were found to zip.")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for entry in entries:
            if entry.is_dir():
                for file_path in entry.rglob("*"):
                    if file_path.is_file():
                        archive.write(file_path, file_path.relative_to(temp_path))
            elif entry.is_file():
                archive.write(entry, entry.name)

    return zip_path


async def make_zip_from_temp_with_progress(temp_path, archive_name=None, progress_callback=None):
    temp_path = Path(temp_path)
    archive_name = safe_filename(archive_name or artifact_name_from_temp(temp_path))
    zip_path = temp_path / f"{archive_name}.zip"

    entries = downloadable_entries(temp_path)
    if not entries:
        raise RuntimeError("No downloaded files were found to zip.")

    files = []
    for entry in entries:
        if entry.is_dir():
            files.extend(file_path for file_path in entry.rglob("*") if file_path.is_file())
        elif entry.is_file():
            files.append(entry)

    total_bytes = sum(file_path.stat().st_size for file_path in files) or 1
    written_bytes = 0
    last_percent = -1

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for file_path in files:
            arcname = file_path.relative_to(temp_path)
            with file_path.open("rb") as source, archive.open(str(arcname), "w") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
                    written_bytes += len(chunk)
                    percent = int((written_bytes / total_bytes) * 100)
                    if progress_callback and percent != last_percent:
                        last_percent = percent
                        await progress_callback(percent)
                    await asyncio.sleep(0)

    if progress_callback:
        await progress_callback(100)
    return zip_path
