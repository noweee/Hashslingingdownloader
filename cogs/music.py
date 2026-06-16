import asyncio
import hashlib
import random
import subprocess
import time
from datetime import timedelta

import discord
from discord.ext import commands

from helpers.audio_quality import detect_audio_quality
from helpers.audio_quality import count_audio_files
from helpers.artifacts import artifact_name_from_temp, make_zip_from_temp_with_progress
from helpers.config import channel_mention, load_config
from helpers.daily_counters import reserve
from helpers.discord_results import create_user_result_channel, delete_channel_later, is_user_result_channel
from helpers.processes import run_logged_command
from helpers.progress import ProgressMessage
from helpers.retention import maybe_delete_oldest_if_near_full, schedule_delete_after, track_upload
from helpers.rclone_paths import remote_path
from helpers.request_context import cleanup_request_context, create_request_context
from helpers.shorteners import shorten_link
from helpers.spotify_bridge import spotify_to_qobuz_search
from helpers.streamrip_config import make_request_streamrip_env
from helpers.tiers import describe_tier, member_tier, requested_quality


config = load_config()

download_folder = config["bot_folder"]
request_channel = config["request_channel"]
upload_channel = config["upload_channel"]


def service_kind(link):
    lowered = link.lower()
    if "spotify" in lowered:
        return "spotify"
    if "qobuz" in lowered:
        return "qobuz"
    return "unsupported"


def content_kind(link):
    lowered = link.lower()
    if any(name in lowered for name in ["album", "playlist"]):
        return "batch"
    if "artist" in lowered:
        return "artist"
    return "track"


def command_for(link, temp_path, qobuz_quality, qobuz_search=None):
    kind = service_kind(link)
    if qobuz_search:
        media_type, query, _song_count = qobuz_search
        streamrip_env = make_request_streamrip_env(temp_path, qobuz_quality)
        return [
            "rip",
            "--quality",
            str(qobuz_quality),
            "search",
            "--first",
            "qobuz",
            media_type,
            query,
        ], "rip_log.txt", "Downloading...", streamrip_env
    if kind == "spotify":
        return [
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
        ], "spotdl_log.txt", "Downloading...", None
    streamrip_env = make_request_streamrip_env(temp_path, qobuz_quality)
    return ["rip", "--quality", str(qobuz_quality), "url", link], "rip_log.txt", "Downloading...", streamrip_env


async def download_searches(searches, temp_path, qobuz_quality, log_prefix, progress):
    total = len(searches)
    failed = []
    streamrip_env = make_request_streamrip_env(temp_path, qobuz_quality)
    for index, (media_type, query, _song_count) in enumerate(searches, start=1):
        await progress.percent("Downloading", ((index - 1) / total) * 100, force=True)
        returncode = await run_logged_command(
            [
                "rip",
                "--quality",
                str(qobuz_quality),
                "search",
                "--first",
                "qobuz",
                media_type,
                query,
            ],
            f"{log_prefix}rip_{index:03d}_log.txt",
            env=streamrip_env,
        )
        if returncode != 0:
            failed.append(query)
        await progress.percent("Downloading", (index / total) * 100, force=True)
    return failed


async def ask_choice(bot, channel, author, prompt, choices, timeout=45):
    choice_text = ", ".join(f"`{choice}`" for choice in choices)
    notice = await channel.send(f"{author.mention} {prompt}\nReply with {choice_text}.")

    def check(message):
        return (
            message.author.id == author.id
            and message.channel.id == channel.id
            and message.content.lower().strip() in choices
        )

    try:
        response = await bot.wait_for("message", timeout=timeout, check=check)
    except asyncio.TimeoutError:
        await notice.edit(content="Request cancelled: no confirmation received.")
        return "cancel"
    return response.content.lower().strip()


async def confirm_downgrade(bot, channel, author, tier, quality_label):
    choice = await ask_choice(
        bot,
        channel,
        author,
        f"Your current tier is **{tier.label}**. Available quality: **{quality_label}**. Continue with that quality or cancel?",
        {"continue", "cancel"},
        timeout=30,
    )
    return choice == "continue"


class Music(commands.Cog, name="music"):
    def __init__(self, bot):
        self.bot = bot
        self.active_users = set()

    @commands.command(name="dl")
    async def dl(self, ctx, link, quality: str | None = None):
        """
        Unified downloader. Tier, quality, and delivery are selected from Discord roles.
        """
        if ctx.channel.id != request_channel:
            await ctx.reply(f"This command can only be used in {channel_mention(request_channel)}")
            return
        if "https" not in link or "." not in link:
            await ctx.reply(f"Please send a valid `https://` link, {ctx.author.mention}.")
            return
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        if ctx.author.id in self.active_users:
            await ctx.send(f"{ctx.author.mention} You already have an active request. Please wait for it to finish before starting another one.")
            return
        self.active_users.add(ctx.author.id)

        request_id, temp_path = create_request_context(download_folder)
        log_prefix = f"{request_id}_"
        up_channel = self.bot.get_channel(upload_channel) or ctx.channel
        result_channel, accepted_message = await create_user_result_channel(ctx, up_channel, request_id)
        await ctx.send(f"{ctx.author.mention} {accepted_message}")
        progress = None

        try:
            tier = member_tier(ctx.author)
            kind = service_kind(link)
            if kind == "unsupported":
                await result_channel.send(
                    f"{ctx.author.mention}, this source is not supported here. Please send a supported download request."
                )
                return
            content = content_kind(link)
            if content == "artist" and not tier.allow_artist_archives:
                await result_channel.send(f"{ctx.author.mention}, artist/archive downloads require **Lifetime Pass**.")
                return
            if content == "batch" and not (tier.allow_albums or tier.allow_playlists):
                await result_channel.send(f"{ctx.author.mention}, your **{tier.label}** allows single tracks only.")
                return

            try:
                quality_choice = requested_quality(quality, tier)
            except ValueError as e:
                await result_channel.send(f"{ctx.author.mention}, {e}")
                return
            if quality_choice is None:
                if not await confirm_downgrade(self.bot, result_channel, ctx.author, tier, tier.quality_label):
                    return
                quality_label, qobuz_quality = tier.quality_label, tier.qobuz_quality
            else:
                quality_label, qobuz_quality = quality_choice

            if quality and qobuz_quality < tier.qobuz_quality:
                choice = await ask_choice(
                    self.bot,
                    result_channel,
                    ctx.author,
                    f"Your **{tier.label}** can use **{tier.quality_label}**, but you requested **{quality_label}**. Proceed with requested quality, switch to highest, or cancel?",
                    {"requested", "highest", "cancel"},
                )
                if choice == "cancel":
                    return
                if choice == "highest":
                    quality_label, qobuz_quality = tier.quality_label, tier.qobuz_quality

            if tier.key == "lifetime" and kind != "spotify" and qobuz_quality < 4:
                choice = await ask_choice(
                    self.bot,
                    result_channel,
                    ctx.author,
                    "Lifetime Pass can try **Atmos / highest available** when the source supports it. Use `atmos`, keep `highest`, or cancel?",
                    {"atmos", "highest", "cancel"},
                )
                if choice == "cancel":
                    return
                if choice in {"atmos", "highest"}:
                    quality_label, qobuz_quality = "Dolby Atmos / highest available when supported", 4

            qobuz_search = None
            qobuz_searches = None
            known_song_count = None
            source_note = None
            if kind == "spotify" and qobuz_quality > 1:
                prep = ProgressMessage(await result_channel.send("Preparing request...\n`[--------------------] 0%`"))
                qobuz_search = await spotify_to_qobuz_search(link, temp_path, f"{log_prefix}spotify_metadata_log.txt")
                await prep.percent("Preparing request", 100, force=True)
                if qobuz_search:
                    media_type, query, _known_song_count = qobuz_search
                    known_song_count = _known_song_count
                    if media_type == "tracks":
                        qobuz_searches = query
                        source_note = f"Request matched as **{len(qobuz_searches)} item(s)**."
                        qobuz_search = None
                    else:
                        source_note = f"Request matched as **{media_type}: {query}**."
                    await result_channel.send(f"{ctx.author.mention} {source_note}")
                else:
                    choice = await ask_choice(
                        self.bot,
                        result_channel,
                        ctx.author,
                        "I could not prepare this at your highest available quality. Proceed with standard quality or cancel?",
                        {"proceed", "cancel"},
                    )
                    if choice == "cancel":
                        return
                    quality_label, qobuz_quality = "Standard quality", 1
            if known_song_count and tier.max_batch_tracks is not None and known_song_count > tier.max_batch_tracks:
                await result_channel.send(
                    f"{ctx.author.mention}, your **{tier.label}** allows up to **{tier.max_batch_tracks}** item(s) per request. "
                    f"This request contains **{known_song_count}** item(s), so it will not be downloaded."
                )
                return
            await result_channel.send(
                f"Accepted as **{tier.label}**. Quality target: **{quality_label}**.\n"
                f"{describe_tier(tier)}"
            )
            progress = ProgressMessage(await result_channel.send(f"{ctx.author.mention} Queued...\n`[--------------------] 0%`"))

            random_rclone_drive = random.choice(config["rclone_drives"])

            download_start_time = time.time()
            if qobuz_searches:
                await progress.set("Downloading...", force=True)
                failed_searches = await download_searches(qobuz_searches, temp_path, qobuz_quality, log_prefix, progress)
                if failed_searches:
                    await result_channel.send(
                        f"{len(failed_searches)} item(s) could not be prepared and were skipped."
                    )
            else:
                command, log_name, download_status, process_env = command_for(link, temp_path, qobuz_quality, qobuz_search)
                await progress.set(download_status, force=True)
                await progress.percent("Downloading", 0, force=True)
                returncode = await run_logged_command(
                    command,
                    f"{log_prefix}{log_name}",
                    env=process_env,
                    progress_callback=lambda percent: progress.percent("Downloading", percent),
                )
                if returncode != 0:
                    raise RuntimeError(f"downloader failed with exit code {returncode}")
            download_time = timedelta(seconds=round(time.time() - download_start_time))
            detected_quality = detect_audio_quality(temp_path)
            song_count = count_audio_files(temp_path)
            if song_count < 1:
                raise RuntimeError("No audio files were downloaded.")
            if tier.max_batch_tracks is not None and song_count > tier.max_batch_tracks:
                await result_channel.send(
                    f"{ctx.author.mention}, your **{tier.label}** allows up to **{tier.max_batch_tracks}** song(s) per request. "
                    f"This request contains **{song_count}** song(s), so it will not be uploaded."
                )
                return
            try:
                used_after_reserve = reserve(ctx.author.id, tier, song_count)
            except RuntimeError as e:
                await result_channel.send(f"{ctx.author.mention} {e} This request contains **{song_count}** song(s), so it will not be uploaded.")
                return
            cap_text = "Unlimited" if tier.daily_cap is None else f"{used_after_reserve}/{tier.daily_cap}"
            await result_channel.send(f"Counted **{song_count}** song(s). Daily usage: **{cap_text}**.")

            zipping_start_time = time.time()
            archive_name = artifact_name_from_temp(temp_path, fallback="Music request")
            zip_path = await make_zip_from_temp_with_progress(
                temp_path,
                archive_name,
                progress_callback=lambda percent: progress.percent("Compiling zip", percent),
            )
            zip_file = zip_path.name
            zipping_time = timedelta(seconds=round(time.time() - zipping_start_time))

            sha256_hash = hashlib.sha256()
            with zip_path.open("rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    sha256_hash.update(chunk)
            checksum = sha256_hash.hexdigest().upper()

            upload_start_time = time.time()
            await progress.percent("Uploading", 0, force=True)
            await maybe_delete_oldest_if_near_full(result_channel, random_rclone_drive)
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
                f"{log_prefix}upload_log.txt",
                progress_callback=lambda percent: progress.percent("Uploading", percent),
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
            output_link = await shorten_link(config, gdrive_link) if tier.ad_supported else gdrive_link
            track_upload(remote_file, zip_file, ctx.author.id, result_channel.id)

            all_done = discord.Embed(
                title="Delivery Ready",
                description=f"{ctx.author.mention}, your package is ready.",
                color=0x2ECC71,
            )
            all_done.add_field(name="Package", value=zip_file, inline=False)
            all_done.add_field(name="Items", value=str(song_count), inline=True)
            all_done.add_field(name="Access", value="Standard" if tier.ad_supported else "Direct", inline=True)
            all_done.add_field(name="Link", value=output_link, inline=False)
            all_done.add_field(name="Processing", value=str(download_time), inline=True)
            all_done.add_field(name="Packaging", value=str(zipping_time), inline=True)
            all_done.add_field(name="Delivery", value=str(upload_time), inline=True)
            all_done.add_field(
                name="Availability",
                value="Deleted after 2 hours, sooner if storage is near the limit, or immediately if you start a new request.",
                inline=False,
            )
            all_done.add_field(name="Checksum", value=checksum, inline=False)
            all_done.set_footer(text="Hash Slinging Downloader")

            cleanup_request_context(temp_path)

            await result_channel.send(embed=all_done)
            await result_channel.send(f"{ctx.author.mention} {output_link}")
            await result_channel.send(
                "Copy the link now. This private download channel will be deleted after 2 hours, "
                "sooner if storage is near the limit, or immediately if you start a new request."
            )
            await progress.set("Complete.", force=True)
            self.bot.loop.create_task(schedule_delete_after(self.bot, remote_file, zip_file, ctx.author.id, result_channel.id))
            if isinstance(result_channel, discord.TextChannel) and is_user_result_channel(result_channel, ctx.author.id):
                self.bot.loop.create_task(delete_channel_later(result_channel))
        except Exception as e:
            if progress:
                await progress.set(f"Failed: {type(e).__name__}: {e}", force=True)
            await result_channel.send(
                f"Download failed: `{type(e).__name__}: {e}`\n"
                "The request could not be completed. Check the bot folder logs on the server machine for details."
            )
        finally:
            cleanup_request_context(temp_path)
            self.active_users.discard(ctx.author.id)


async def setup(bot):
    await bot.add_cog(Music(bot))
