import discord


async def set_request_channel_locked(channel, role, locked):
    try:
        await channel.set_permissions(role, send_messages=not locked)
        return True
    except discord.Forbidden:
        return False
