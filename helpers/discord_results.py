import asyncio

import discord


def channel_safe_name(value):
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part)[:40] or "user"


def result_channel_topic(user_id):
    return f"Hash Slinging Downloader private channel for user {user_id}"


def is_user_result_channel(channel, user_id):
    return getattr(channel, "topic", None) == result_channel_topic(user_id)


async def delete_channel_later(channel, delay_seconds=7200):
    await asyncio.sleep(delay_seconds)
    try:
        await channel.delete(reason="Private download channel expired")
    except Exception:
        pass


async def delete_existing_result_channel(guild, user_id):
    topic = result_channel_topic(user_id)
    for channel in guild.text_channels:
        if getattr(channel, "topic", None) == topic:
            try:
                await channel.send("A new request was started. This previous private download channel will be deleted now.")
            except Exception:
                pass
            try:
                await channel.delete(reason="User started a new private download request")
            except Exception:
                pass


async def create_user_result_channel(ctx, upload_target, request_id):
    if not ctx.guild:
        return upload_target, "Request accepted, but I could not create a private server channel."

    await delete_existing_result_channel(ctx.guild, ctx.author.id)

    name = f"download-{channel_safe_name(ctx.author.display_name)}"
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
    }
    try:
        channel = await ctx.guild.create_text_channel(
            name=name,
            overwrites=overwrites,
            category=getattr(upload_target, "category", None),
            topic=result_channel_topic(ctx.author.id),
            reason=f"Private download result channel {request_id}",
        )
        return channel, (
            f"Request accepted. Private result channel: {channel.mention}\n"
            "This channel will be automatically deleted after 2 hours, sooner if storage is near the limit, "
            "or immediately if you start a new request."
        )
    except Exception:
        return upload_target, "Request accepted, but I could not create a private result channel. Results will appear in the upload channel."
