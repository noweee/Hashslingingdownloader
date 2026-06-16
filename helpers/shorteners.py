import asyncio
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _shorten_sync(config, url):
    api_key = config.get("shrinkearn_api_key")
    if not api_key:
        return url

    api_url = config.get("shrinkearn_api_url", "https://shrinkearn.com/api")
    query = urlencode({"api": api_key, "url": url})
    request = Request(
        f"{api_url}?{query}",
        headers={"User-Agent": "Mozilla/5.0 HashSlingingDownloader/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read().decode("utf-8").strip()
    except HTTPError as exc:
        if exc.code == 403:
            raise RuntimeError("The link shortener returned 403 Forbidden. Check the shortener API key and account access.") from exc
        raise

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return data

    if payload.get("status") == "success" and payload.get("shortenedUrl"):
        return payload["shortenedUrl"]
    if payload.get("shortenedUrl"):
        return payload["shortenedUrl"]
    raise RuntimeError(payload.get("message", "The link shortener did not return a shortened URL."))


async def shorten_link(config, url):
    return await asyncio.to_thread(_shorten_sync, config, url)
