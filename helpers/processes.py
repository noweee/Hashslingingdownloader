import asyncio
import sys

from helpers.progress import extract_percent


async def run_logged_command(command, log_path, progress_callback=None, env=None, append=False, header=None):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
    )

    mode = "ab" if append else "wb"
    with open(log_path, mode) as log_file:
        if header:
            log_file.write((header.rstrip() + "\n").encode("utf-8"))
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            sys.stdout.buffer.write(line)
            log_file.write(line)
            if progress_callback:
                percent = extract_percent(line.decode("utf-8", errors="ignore"))
                if percent is not None:
                    await progress_callback(percent)

    return await process.wait()
