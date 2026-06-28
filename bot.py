import json
import os
import platform
from datetime import datetime

import discord
from colorama import Fore, Style
from discord.ext import commands

from helpers.config import channel_mention, load_config
from helpers.admin import get_admin_channel


config = load_config()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class HashSlingingDownloaderBot(commands.Bot):
    async def setup_hook(self):
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"cogs.{extension}")
                    print(f"Loaded extension '{extension}'")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Failed to load extension {extension}\n{exception}")


bot = HashSlingingDownloaderBot(command_prefix=config["bot_prefix"], intents=intents)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(Fore.MAGENTA + f"{bot.user.name} is online. Hash Slinging Downloader is ready.")
    print(Fore.RED + "-------------------")
    print(Fore.GREEN + f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print(Fore.RED + "-------------------")
    print(Style.RESET_ALL)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Hash Slinging Downloader"))
    for guild in bot.guilds:
        await get_admin_channel(guild)


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    if message.guild and message.channel.id == config.get("request_channel"):
        prefix = str(config.get("bot_prefix", "h!")).lower()
        content = (message.content or "").strip().lower()
        admin_commands = ("mc", "minecraft", "server", "ping", "clean", "cleanlogs", "hardreset", "purgegd")
        allowed = content.startswith(f"{prefix}dl") or any(
            content == f"{prefix}{name}" or content.startswith(f"{prefix}{name} ")
            for name in admin_commands
        )
        if not allowed:
            try:
                await message.delete()
            except Exception:
                pass
            return
    with open("blacklist.json") as file:
        blacklist = json.load(file)
    if message.author.id in blacklist["ids"]:
        return
    await bot.process_commands(message)


@bot.event
async def on_command_completion(ctx):
    executed_command = ctx.command.qualified_name.split(" ")[0]
    print(
        Fore.YELLOW
        + f"Executed {executed_command} command in {ctx.guild.name} "
        + f"(ID: {ctx.message.guild.id}) by {ctx.message.author} "
        + f"(ID: {ctx.message.author.id})"
    )
    print(Style.RESET_ALL)

    log_channel = bot.get_channel(config.get("log_channel"))
    if log_channel:
        timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed = discord.Embed(
            title="Bot Action Log",
            description=f"Executed `{executed_command}` command by <@{ctx.message.author.id}> at `{timenow}`",
            color=0xBF40BF,
        )
        await log_channel.send(embed=embed)


@bot.event
async def on_command_error(context, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            title="Hey, please slow down! You're stressing me out!",
            description=f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="You are missing the permission `" + ", ".join(error.missing_perms) + "` to execute this command!",
            color=0xE02B2B,
        )
        await context.reply(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Wait a minute...",
            description=str(error).capitalize(),
            color=0xE02B2B,
        )
        embed.set_footer(text="Use the request channel for downloads.")
        await context.reply(embed=embed)
    elif isinstance(error, commands.MaxConcurrencyReached):
        embed = discord.Embed(
            title="Whoops! Not too fast!",
            description="Please wait for the previous downloads to finish.\nTry again later.",
            color=0xE02B2B,
        )
        embed.set_footer(text=f"Requested by {context.message.author}.")
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingAnyRole):
        embed = discord.Embed(
            title="Sorry!",
            description=f"Only allowed roles can use this command. Refer to {channel_mention(config.get('supporter_channel'))} for more info.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRole):
        embed = discord.Embed(
            title="Sorry!",
            description="You do not have the required role to use this command.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
        embed = discord.Embed(
            title="Missing bot permission",
            description="Discord refused that action. Move the bot role above the affected channel/roles, or give it the needed permission.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)
    else:
        raise error


bot.run(config["token"])
