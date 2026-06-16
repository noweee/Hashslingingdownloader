import json
from pathlib import Path

from helpers.processes import run_logged_command


def spotify_media_type(link):
    lowered = link.lower()
    if "album" in lowered:
        return "album"
    if "playlist" in lowered:
        return "playlist"
    return "track"


def spotify_query_from_items(items, media_type):
    if not items:
        return None
    first = items[0]
    if media_type == "track":
        artist = first.get("artist") or first.get("artists") or first.get("album_artist")
        title = first.get("name") or first.get("title")
        return " - ".join(part for part in [artist, title] if part)
    if media_type == "album":
        artist = first.get("album_artist") or first.get("artist") or first.get("artists")
        album = first.get("album_name") or first.get("album")
        return " - ".join(part for part in [artist, album] if part)
    list_name = first.get("list_name")
    if isinstance(list_name, list):
        list_name = next((name for name in list_name if name), None)
    return list_name


async def spotify_to_qobuz_search(link, temp_path, log_path):
    metadata_path = Path(temp_path) / "spotify_metadata.spotdl"
    returncode = await run_logged_command(
        ["spotdl", "save", link, "--save-file", str(metadata_path)],
        log_path,
    )
    if returncode != 0 or not metadata_path.is_file():
        return None
    try:
        items = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    media_type = spotify_media_type(link)
    query = spotify_query_from_items(items, media_type)
    if not query:
        return None
    return media_type, query, max(1, len(items))
