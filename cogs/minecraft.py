import discord
from discord.ext import commands, tasks

from helpers.config import load_config
from helpers.minecraft_status import format_system_uptime, query_minecraft_status


config = load_config()


class Minecraft(commands.Cog, name="minecraft"):
    def __init__(self, bot):
        self.bot = bot
        self.host = config.get("minecraft_host", "127.0.0.1")
        self.port = config.get("minecraft_port", 25565)
        self.name = config.get("minecraft_name", "Hash Slinging Server")
        self.status_interval = config.get("minecraft_status_interval", 60)
        self.update_presence.change_interval(seconds=self.status_interval)
        self.update_presence.start()

    def cog_unload(self):
        self.update_presence.cancel()

    @tasks.loop(seconds=60)
    async def update_presence(self):
        status = await query_minecraft_status(self.host, self.port)
        uptime = format_system_uptime()
        if status.online:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"MC online - up {uptime}",
            )
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
        else:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"MC offline - up {uptime}",
            )
            await self.bot.change_presence(status=discord.Status.idle, activity=activity)

    @update_presence.before_loop
    async def before_update_presence(self):
        await self.bot.wait_until_ready()

    @commands.command(name="mc", aliases=["minecraft", "server"])
    async def minecraft(self, context):
        """
        Show Minecraft server status and server power-on time.
        """
        async with context.typing():
            status = await query_minecraft_status(self.host, self.port)
            uptime = format_system_uptime()

        if status.online:
            color = 0x2ECC71
            title = f"{self.name} is online"
            players = "Unknown"
            if status.players_online is not None and status.players_max is not None:
                players = f"{status.players_online}/{status.players_max}"
            description = f"`{self.host}:{self.port}` is accepting Minecraft connections."
        else:
            color = 0xE02B2B
            title = f"{self.name} is offline"
            players = "Offline"
            description = f"`{self.host}:{self.port}` is not accepting Minecraft connections."

        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name="Power on time", value=uptime, inline=True)
        embed.add_field(name="Players", value=players, inline=True)
        embed.add_field(name="Latency", value=f"{status.latency_ms}ms" if status.latency_ms is not None else "N/A", inline=True)
        embed.add_field(name="Version", value=status.version or "Unknown", inline=True)
        if status.error:
            embed.add_field(name="Check result", value=status.error[:1000], inline=False)
        embed.set_footer(text=f"Requested by {context.message.author}")
        await context.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Minecraft(bot))
