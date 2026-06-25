import re
import time

import discord


def progress_bar(percent, width=20):
    percent = max(0, min(100, int(percent)))
    filled = round((percent / 100) * width)
    return f"[{'#' * filled}{'-' * (width - filled)}] {percent}%"


def _progress_color(stage):
    stage = (stage or "").lower()
    if "fail" in stage or "error" in stage:
        return 0xE74C3C
    if "complete" in stage or "done" in stage:
        return 0x2ECC71
    if "upload" in stage:
        return 0xF39C12
    if "zip" in stage or "pack" in stage:
        return 0x9B59B6
    if "download" in stage:
        return 0x3498DB
    if "queue" in stage:
        return 0x95A5A6
    return 0x5865F2


def build_progress_embed(stage, percent=None, requester=None, note=None):
    embed = discord.Embed(
        title="Request Status",
        description="Live updates for the current download request.",
        color=_progress_color(stage),
    )
    embed.add_field(name="Stage", value=stage or "Working", inline=False)
    if percent is not None:
        embed.add_field(name="Progress", value=f"`{progress_bar(percent)}`", inline=False)
    if requester:
        embed.add_field(name="Requester", value=requester, inline=True)
    if note:
        embed.add_field(name="Note", value=note, inline=False)
    embed.set_footer(text="Hash Slinging Downloader")
    return embed


class ProgressMessage:
    def __init__(self, message, requester=None):
        self.message = message
        self.requester = requester
        self.last_text = None
        self.last_edit = 0
        self.last_percent = {}
        self.stage = "Working"
        self.note = None
        self.percent_label = None
        self.percent_value = None

    def _build_embed(self):
        embed = build_progress_embed(
            self.stage,
            self.percent_value,
            requester=self.requester,
            note=self.note,
        )
        return embed

    async def set(self, text, force=False):
        now = time.monotonic()
        if not force and text == self.last_text:
            return
        if not force and now - self.last_edit < 2:
            return
        self.last_text = text
        self.last_edit = now
        self.stage = text
        await self.message.edit(embed=self._build_embed(), content=None)

    async def percent(self, label, percent, force=False):
        percent = max(0, min(100, int(percent)))
        last = self.last_percent.get(label)
        if not force and last is not None and percent - last < 5 and percent < 100:
            return
        self.last_percent[label] = percent
        self.stage = label
        self.percent_label = label
        self.percent_value = percent
        await self.message.edit(embed=self._build_embed(), content=None)


def extract_percent(text):
    matches = re.findall(r"(\d{1,3})\s*%", text)
    if not matches:
        return None
    return max(0, min(100, int(matches[-1])))
