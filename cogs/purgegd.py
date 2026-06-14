from pathlib import Path
import subprocess

import discord
from discord.ext import commands

from helpers.config import load_config


config = load_config()


class SBPHRclone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purgegd")
    @commands.has_role("Dev and Maintainer")
    async def purge_gd(self, ctx):
        """
        Purges and cleans the configured RClone remote. Only Admin/Dev can use this command.
        """
        remote = config["rclone_drives"][0]
        try:
            await ctx.message.add_reaction("⏳")
            proc = subprocess.Popen(
                ["rclone", "delete", f"{remote}:", "--drive-use-trash=false", "-vv"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logs = ""
            while proc.poll() is None:
                line = proc.stdout.readline().decode()
                if line:
                    print(line.rstrip())
                    logs += line
            stdout, stderr = proc.communicate()
            logs += stdout.decode() + stderr.decode()

            log_path = Path(config["bot_folder"]) / "rclone_logs.txt"
            log_path.write_text(
                "=================================================================================\n"
                f"LOGS FOR RCLONE REMOTE {remote}, CHECK LINES BELOW ON WHAT THIS COMMAND DELETED!\n"
                "=================================================================================\n"
                + logs
            )
            await ctx.message.add_reaction("✅")
            await ctx.reply(
                f"`{remote}:` storage contents purged successfully.\nRClone logs attached below.",
                file=discord.File(str(log_path)),
            )
        except subprocess.CalledProcessError as e:
            await ctx.message.add_reaction("❌")
            await ctx.reply(f"Failed to purge storage, reason: {e}")

async def setup(bot):
    await bot.add_cog(SBPHRclone(bot))
