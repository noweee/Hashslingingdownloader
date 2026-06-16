import os
import platform

import discord
from discord.ext import commands

from helpers.config import load_config
from helpers.filesystem import clean_temp_dir


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

    @commands.command(name="ping")
    async def ping(self, context):
        """
        Check if the bot is online.
        """
        embed = discord.Embed(
            title="Pong",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0x2ECC71,
        )
        await context.reply(embed=embed)

    @commands.command(name="invite", aliases=["support", "supportserver"])
    async def invite(self, context):
        """
        Get the community invite link.
        """
        embed = discord.Embed(
            description="Ask a staff member for the current Hash Slinging Downloader Community invite.",
            color=0x2ECC71,
        )
        await context.reply(embed=embed)

    @commands.command(name="clean")
    @commands.has_any_role("Dev and Maintainer")
    async def clean(self, context):
        """
        Cleans temporary request files. Only Admin/Dev can use this command.
        """
        clean_temp_dir(download_folder)
        embed = discord.Embed(
            title="Cleaned",
            description="Temporary request files were removed.",
            color=0x2ECC71,
        )
        await context.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
