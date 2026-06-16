from discord.ext import commands


class Qdl(commands.Cog, name="qdl"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="qdl", hidden=True)
    async def dl(self, ctx, *, link=None):
        """Deprecated. Use h!dl <link> [quality] instead."""
        await ctx.reply(
            "Use `h!dl <qobuz-link> [quality]` instead. Quality and delivery are now chosen from your Discord roles."
        )


async def setup(bot):
    await bot.add_cog(Qdl(bot))
