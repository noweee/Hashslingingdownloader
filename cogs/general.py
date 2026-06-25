import asyncio
import os
import platform
import subprocess
import sys
from pathlib import Path

import discord
from discord.ext import commands

from helpers.config import load_config
from helpers.filesystem import clean_log_files, clean_upload_registry
from helpers.discord_results import delete_private_request_channels
from helpers.admin import is_admin_channel, send_admin_output


config = load_config()
download_folder = config["bot_folder"]


class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="info", aliases=["botinfo"])
    async def info(self, context):
        """
        Get information about Hash Slinging Downloader.
        """
        embed = discord.Embed(
            title="Hash Slinging Downloader",
            description="Private download assistant for the Hash Slinging Downloader Community.",
            color=0x2ECC71,
        )
        embed.add_field(name="Python", value=f"{platform.python_version()}", inline=True)
        embed.add_field(name="Prefix", value=f"{config['bot_prefix']}", inline=True)
        embed.add_field(name="Host", value=f"{platform.system()} {platform.release()} ({os.name})", inline=False)
        embed.set_footer(text=f"Requested by {context.message.author}")
        await context.reply(embed=embed)

    @commands.command(name="invite", aliases=["support", "supportserver"])
    async def invite(self, context):
        """
        Get the community invite link.
        """
        embed = discord.Embed(
            description="Join the Hash Slinging Downloader Community:\nhttps://discord.gg/JH6waCG55h",
            color=0x2ECC71,
        )
        await context.reply(embed=embed)

    @commands.command(name="clean", hidden=True)
    @commands.has_any_role("Dev and Maintainer", "Founders")
    async def clean(self, context):
        """
        Cleans temporary request files. Only Admin/Dev can use this command.
        """
        if not is_admin_channel(context.channel):
            await context.reply("Use this command in #admin-commands-hsd.")
            return
        clean_temp_dir(download_folder)
        embed = discord.Embed(
            title="Cleaned",
            description="Temporary request files were removed.",
            color=0x2ECC71,
        )
        await send_admin_output(context, embed=embed)

    @commands.command(name="ping", hidden=True)
    @commands.has_any_role("Dev and Maintainer", "Founders")
    async def ping(self, context):
        """
        Check if the bot is online.
        """
        if not is_admin_channel(context.channel):
            await context.reply("Use this command in #admin-commands-hsd.")
            return
        embed = discord.Embed(
            title="Pong",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0x2ECC71,
        )
        await send_admin_output(context, embed=embed)

    @commands.command(name="cleanlogs", hidden=True)
    @commands.has_any_role("Dev and Maintainer", "Founders")
    async def cleanlogs(self, context):
        """
        Removes log files created by download requests.
        """
        if not is_admin_channel(context.channel):
            await context.reply("Use this command in #admin-commands-hsd.")
            return
        log_removed = clean_log_files(download_folder)
        request_removed = clean_request_folders(download_folder)
        registry_removed = clean_upload_registry(download_folder)
        embed = discord.Embed(
            title="Logs cleaned",
            description=(
                f"Removed **{len(log_removed)}** log file(s), "
                f"**{len(request_removed)}** old request folder(s), "
                f"and {'removed' if registry_removed else 'kept'} the upload registry."
            ),
            color=0x2ECC71,
        )
        await send_admin_output(context, embed=embed)

    @commands.command(name="hardreset", hidden=True)
    @commands.has_any_role("Dev and Maintainer", "Founders")
    async def hardreset(self, context):
        """
        Clean the drive, clear logs, and restart the bot.
        """
        if not is_admin_channel(context.channel):
            await context.reply("Use this command in #admin-commands-hsd.")
            return

        await send_admin_output(context, content="Hard reset started. Cleaning storage and local files...")

        log_removed = clean_log_files(download_folder)
        registry_removed = clean_upload_registry(download_folder)
        private_removed = 0
        for guild in self.bot.guilds:
            removed = await delete_private_request_channels(guild)
            private_removed += len(removed)

        for remote in config.get("rclone_drives", []):
            try:
                await asyncio.to_thread(
                    subprocess.run,
                    ["rclone", "delete", f"{remote}:", "--drive-use-trash=false"],
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

        restart_script = Path(__file__).resolve().parents[1] / "bot.py"
        subprocess.Popen([sys.executable, str(restart_script)], cwd=str(restart_script.parent))

        await send_admin_output(
            context,
            content=(
                "Hard reset finished. "
                f"Removed **{len(log_removed)}** log file(s), "
                f"deleted **{private_removed}** private request channel(s), "
                f"{'removed' if registry_removed else 'kept'} the upload registry, and restarted the bot."
            ),
        )
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(General(bot))
