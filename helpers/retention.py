import asyncio
import re
import subprocess

from helpers.upload_registry import add_upload, oldest_upload, remove_upload


async def delete_remote_file(remote_file):
    result = await asyncio.to_thread(
        subprocess.run,
        ["rclone", "deletefile", remote_file],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        remove_upload(remote_file)
    return result.returncode == 0


async def schedule_delete_after(bot, remote_file, display_name, user_id, channel_id, delay_seconds=7200):
    await asyncio.sleep(delay_seconds)
    deleted = await delete_remote_file(remote_file)
    user = bot.get_user(user_id)
    channel = bot.get_channel(channel_id)
    text = f"`{display_name}` has been deleted after 2 hours." if deleted else f"Automatic deletion failed for `{display_name}`."
    if user:
        try:
            await user.send(text)
            return
        except Exception:
            pass
    if channel:
        await channel.send(text)


def _parse_bytes(text, label):
    match = re.search(rf"{label}:\s+([0-9.]+)\s+([KMGTPE]?i?B)", text, re.IGNORECASE)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    multipliers = {
        "b": 1,
        "kb": 1000,
        "mb": 1000**2,
        "gb": 1000**3,
        "tb": 1000**4,
        "kib": 1024,
        "mib": 1024**2,
        "gib": 1024**3,
        "tib": 1024**4,
    }
    return value * multipliers.get(unit, 1)


async def maybe_delete_oldest_if_near_full(channel, remote, threshold=0.95):
    result = await asyncio.to_thread(
        subprocess.run,
        ["rclone", "about", f"{remote}:"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return
    used = _parse_bytes(result.stdout, "Used")
    total = _parse_bytes(result.stdout, "Total")
    if not used or not total or used / total < threshold:
        return
    item = oldest_upload()
    if not item:
        return
    await channel.send(f"Drive is near capacity. Deleting oldest tracked file `{item.get('display_name', item['remote_file'])}` early.")
    if await delete_remote_file(item["remote_file"]):
        await channel.send(f"Deleted `{item.get('display_name', item['remote_file'])}` to free space.")


def track_upload(remote_file, display_name, user_id, channel_id):
    add_upload(remote_file, display_name, user_id, channel_id)
