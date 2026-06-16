import json
import os
import sys

import discord
from discord.ext import commands
from helpers.config import load_config

config = load_config()


class Help(commands.Cog, name="help"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, context):
        """
        List all commands Hash Slinging Downloader supports.
        """
        prefix = config["bot_prefix"]
        if not isinstance(prefix, str):
            prefix = prefix[0]
        embed = discord.Embed(title="Help", description="Hash Slinging Downloader commands:", color=0x2ECC71)
        for cog_name, cog in self.bot.cogs.items():
            commands = [command for command in cog.get_commands() if not command.hidden]
            if commands:
                command_list = [command.name for command in commands]
                command_description = [command.help for command in commands]
                help_text = '\n'.join(f'{prefix}{n} - {h}' for n, h in zip(command_list, command_description))
                embed.add_field(name=cog_name.capitalize(), value=f'```{help_text}```', inline=False)
        await context.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
