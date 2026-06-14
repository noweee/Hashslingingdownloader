import hashlib
import random
import subprocess
import sys
import time
from datetime import timedelta

import discord
from discord.ext import commands

from helpers.artifacts import artifact_name_from_temp, make_zip_from_temp
from helpers.config import channel_mention, load_config
from helpers.discord_permissions import set_request_channel_locked
from helpers.filesystem import clean_temp_dir, ensure_temp_dir
from helpers.processes import run_logged_command
from helpers.rclone_cleanup import replace_last_upload
from helpers.rclone_paths import remote_path
from helpers.shorteners import shorten_link


config = load_config()

download_folder = config["bot_folder"]
request_channel = config["request_channel"]
upload_channel = config["upload_channel"]


class SpotDL(commands.Cog, name="spotdl"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="spotdl")
    async def dl(self, ctx, link):
        """
        Downloads music from Spotify.
        """
        req_channel = self.bot.get_channel(request_channel)
        up_channel = self.bot.get_channel(upload_channel)

        if ctx.channel.id != request_channel:
            await ctx.reply(f"This command can only be used in {channel_mention(request_channel)}")
            return

        if "artist" in link:
            await ctx.reply(f"{ctx.author.mention}, downloading Spotify artist profiles is not allowed.")
            return
        if any(service in link for service in ["tidal", "soundcloud", "qobuz", "deezer", "youtube", "youtu.be", "m.youtube"]):
            await ctx.reply(f"{ctx.author.mention}, use `h!dl <link>` for non-Spotify links.")
            return
        if "bandcamp" in link:
            await ctx.reply(f"{ctx.author.mention}, for Bandcamp downloads, use `h!bcdl <link>`.")
            return
        if "https" not in link or ".com" not in link:
            await ctx.reply(f"Please send a valid `https://` Spotify link, {ctx.author.mention}.")
            return

        random_rclone_drive = random.choice(config["rclone_drives"])
        await set_request_channel_locked(req_channel, ctx.guild.default_role, True)
        await ctx.message.add_reaction("✅")
        await ctx.reply(
            f"{ctx.author.mention}, please wait while your request is being downloaded. "
            f"You will receive a ping in {channel_mention(upload_channel)} with your download link once it's done."
        )

        try:
            download_start_time = time.time()
            clean_temp_dir(download_folder)
            temp_path = ensure_temp_dir(download_folder)

            await ctx.message.add_reaction("📁")
            await ctx.message.add_reaction("📥")
            returncode = await run_logged_command(
                [
                    "spotdl",
                    "download",
                    link,
                    "--output",
                    str(temp_path),
                    "--preload",
                    "--sponsor-block",
                    "--print-errors",
                    "--format",
                    "m4a",
                ],
                "spotdl_log.txt",
            )
            if returncode != 0:
                raise RuntimeError(f"spotdl failed with exit code {returncode}")

            download_time = timedelta(seconds=round(time.time() - download_start_time))

            await ctx.message.add_reaction("📦")
            zipping_start_time = time.time()
            archive_name = artifact_name_from_temp(temp_path, fallback="Spotify playlist")
            zip_path = make_zip_from_temp(temp_path, archive_name)
            zip_file = zip_path.name
            zipping_time = timedelta(seconds=round(time.time() - zipping_start_time))

            await ctx.message.add_reaction("🔒")
            sha256_hash = hashlib.sha256()
            with zip_path.open("rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    sha256_hash.update(chunk)
            checksum = sha256_hash.hexdigest().upper()

            await ctx.message.add_reaction("📤")
            upload_start_time = time.time()
            returncode = await run_logged_command(
                [
                    "rclone",
                    "copy",
                    str(zip_path),
                    remote_path(random_rclone_drive, config.get("rclone_upload_path")),
                    "--progress",
                    "--transfers",
                    "16",
                    "--drive-chunk-size",
                    "32M",
                ],
                "upload_log.txt",
            )
            if returncode != 0:
                raise RuntimeError(f"rclone upload failed with exit code {returncode}")
            upload_time = timedelta(seconds=round(time.time() - upload_start_time))

            remote_file = remote_path(random_rclone_drive, config.get("rclone_upload_path"), zip_file)
            link_process = subprocess.run(
                ["rclone", "link", remote_file, "--retries", "15"],
                stdout=subprocess.PIPE,
                encoding="utf-8",
                check=True,
            )
            gdrive_link = link_process.stdout.strip()
            output_link = await shorten_link(config, gdrive_link)
            await replace_last_upload(up_channel, remote_file, zip_file)

            all_done = discord.Embed(
                title="Request complete",
                description="Request complete. The previous uploaded file, if any, has been deleted.",
                color=0x20E84F,
            )
            all_done.add_field(name="Name", value=zip_file, inline=False)
            all_done.add_field(name="Request Link", value=link, inline=False)
            all_done.add_field(name="Download Link", value=output_link, inline=False)
            all_done.add_field(name="Download Time", value=download_time, inline=False)
            all_done.add_field(name="Zip Time", value=zipping_time, inline=False)
            all_done.add_field(name="Upload Time", value=upload_time, inline=False)
            all_done.add_field(name="Retention", value="Deleted when the next request is ready.", inline=False)
            all_done.add_field(name="SHA-256 Checksum", value=checksum, inline=False)
            all_done.set_footer(text=f"Requested by {ctx.message.author}")

            clean_temp_dir(download_folder)

            await up_channel.send(embed=all_done)
            await up_channel.send(f"{ctx.author.mention} {output_link}")
            await ctx.message.add_reaction("👍")
            await req_channel.send(f"Request complete! Download link sent on {channel_mention(upload_channel)}.")
            await set_request_channel_locked(req_channel, ctx.guild.default_role, False)

        except Exception as e:
            await ctx.message.add_reaction("❌")
            await ctx.send(
                f"Download failed: `{type(e).__name__}: {e}`\n"
                "Check `spotdl_log.txt` or `upload_log.txt` in the bot folder for details."
            )
            await set_request_channel_locked(req_channel, ctx.guild.default_role, False)


async def setup(bot):
    await bot.add_cog(SpotDL(bot))
