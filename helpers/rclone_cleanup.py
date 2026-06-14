import asyncio
import subprocess

from helpers.upload_state import get_last_upload, set_last_upload


async def replace_last_upload(channel, remote_file, display_name):
    previous = get_last_upload()
    if previous and previous.get("remote_file") and previous["remote_file"] != remote_file:
        result = await asyncio.to_thread(
            subprocess.run,
            ["rclone", "deletefile", previous["remote_file"]],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            await channel.send(f"Previous file `{previous.get('display_name', previous['remote_file'])}` was deleted because a new request is ready.")
        else:
            await channel.send(f"Could not delete previous file `{previous.get('display_name', previous['remote_file'])}`. Check RClone permissions.")
    set_last_upload(remote_file, display_name)
