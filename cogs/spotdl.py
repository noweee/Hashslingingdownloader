from discord.ext import commands


class SpotDL(commands.Cog, name="spotdl"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="spotdl", hidden=True)
    async def dl(self, ctx, *, link=None):
        """Deprecated. Use h!dl <link> instead."""
        await ctx.reply(
            "Use `h!dl <spotify-link>` instead. Quality and delivery are now chosen from your Discord roles."
        )


async def setup(bot):
    await bot.add_cog(SpotDL(bot))
