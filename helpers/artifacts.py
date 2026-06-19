import re
import zipfile
from pathlib import Path
import asyncio

from helpers.audio_quality import AUDIO_EXTENSIONS


IGNORED_NAMES = {".spotdl-cache", ".streamrip_appdata"}


def strip_quality_tags(name):
    name = re.sub(
        r"\s*[\[(][^\])]*(?:flac|mp3|m4a|aac|alac|wav|ogg|opus|lossless|hi-?res|dolby|atmos|"
        r"(?:16|24)[-\s]?bit|(?:44\.1|48|88\.2|96|176\.4|192)\s?khz|[0-9]{2,4}\s?kbps)[^\])]*[\])]",
        "",
        name,
        flags=re.IGNORECASE,
    )
    trailing_quality = re.compile(
        r"[\s._-]+(?:flac|mp3|m4a|aac|alac|wav|ogg|opus|lossless|hi-?res|dolby\s+atmos|atmos|"
        r"(?:16|24)[-\s]?bit|(?:44\.1|48|88\.2|96|176\.4|192)\s?khz|[0-9]{2,4}\s?kbps)$",
        re.IGNORECASE,
    )
    previous = None
    while previous != name:
        previous = name
        name = trailing_quality.sub("", name).strip()
    return name


def safe_filename(name):
    name = strip_quality_tags(name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "download"


def downloadable_entries(temp_path):
    temp_path = Path(temp_path)
    return [
        entry
        for entry in temp_path.iterdir()
        if entry.name not in IGNORED_NAMES
        and not entry.name.startswith(".")
        and not entry.name.lower().endswith(".zip")
        and not entry.name.lower().endswith(".spotdl")
        and (
            (entry.is_file() and entry.suffix.lower() in AUDIO_EXTENSIONS)
            or entry.is_dir()
        )
    ]


def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def normalize_download_names(temp_path):
    temp_path = Path(temp_path)
    for path in sorted(temp_path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        clean_name = safe_filename(path.stem) + path.suffix if path.is_file() else safe_filename(path.name)
        if clean_name != path.name:
            path.rename(unique_path(path.with_name(clean_name)))


def artifact_name_from_temp(temp_path, fallback="download"):
    normalize_download_names(temp_path)
    entries = downloadable_entries(temp_path)
    if not entries:
        raise RuntimeError("Downloader finished but did not create any files.")
    if len(entries) == 1:
        entry = entries[0]
        return safe_filename(entry.stem if entry.is_file() else entry.name)
    return safe_filename(fallback or "playlist")


def clean_relative_dirs(path):
    path = Path(path)
    if len(path.parts) <= 1:
        return path
    return Path(*(safe_filename(part) for part in path.parts[:-1])) / path.name


def archive_name_for(temp_path, file_path, archive_name, entries):
    temp_path = Path(temp_path)
    if len(entries) == 1 and entries[0].is_dir():
        relative = file_path.relative_to(entries[0])
    else:
        relative = file_path.relative_to(temp_path)
    return Path(archive_name) / clean_relative_dirs(relative)


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
                        archive.write(file_path, archive_name_for(temp_path, file_path, archive_name, entries))
            elif entry.is_file():
                archive.write(entry, Path(archive_name) / entry.name)

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
            arcname = archive_name_for(temp_path, file_path, archive_name, entries)
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
