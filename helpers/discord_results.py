import asyncio

import discord

from helpers.admin import help_members, help_roles


REQUEST_CATEGORY_NAME = "Music Requests"


def channel_safe_name(value):
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part)[:40] or "user"


def request_channel_topic(user_id):
    return f"Hash Slinging Downloader private channel for user {user_id}"


def is_user_result_channel(channel, user_id):
    return getattr(channel, "topic", None) == request_channel_topic(user_id)


def is_private_request_channel(channel):
    topic = getattr(channel, "topic", None) or ""
    category_name = getattr(getattr(channel, "category", None), "name", None)
    return (
        topic.startswith("Hash Slinging Downloader private channel for user ")
        or topic.startswith("Hash Slinging Downloader help channel for user ")
        or category_name == REQUEST_CATEGORY_NAME and getattr(channel, "name", "").startswith(("download-", "help-"))
    )


async def delete_channel_later(channel, delay_seconds=7200):
    await asyncio.sleep(delay_seconds)
    try:
        await channel.delete(reason="Private download channel expired")
    except Exception:
        pass


async def delete_existing_request_channel(guild, user_id):
    topic = request_channel_topic(user_id)
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


async def delete_private_request_channels(guild):
    removed = []
    for channel in list(getattr(guild, "text_channels", [])):
        if not is_private_request_channel(channel):
            continue
        try:
            await channel.delete(reason="Hard reset removed private request channels")
            removed.append(channel)
        except Exception:
            pass
    return removed


async def create_private_request_channel(ctx, upload_target, request_id):
    if not ctx.guild:
        return upload_target, "Request accepted, but I could not create a private server channel."

    await delete_existing_request_channel(ctx.guild, ctx.author.id)

    category = discord.utils.get(ctx.guild.categories, name=REQUEST_CATEGORY_NAME)
    if category is None:
        try:
            category = await ctx.guild.create_category(
                REQUEST_CATEGORY_NAME,
                reason="Hash Slinging Downloader request category",
            )
        except Exception:
            category = getattr(ctx.channel, "category", None)

    name = f"download-{channel_safe_name(ctx.author.display_name)}"
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
    }
    for role in getattr(ctx.guild, "roles", []):
        if role != ctx.guild.default_role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=False)
    try:
        channel = await ctx.guild.create_text_channel(
            name=name,
            overwrites=overwrites,
            category=category,
            topic=request_channel_topic(ctx.author.id),
            reason=f"Private download request channel {request_id}",
        )
        return channel, (
            f"Request accepted. Private request channel: {channel.mention}\n"
            "This channel is private to you and the bot. Use the help button if you need dev access.\n"
            "This channel will be automatically deleted after 2 hours, sooner if storage is near the limit, "
            "or immediately if you start a new request."
        )
    except Exception:
        return upload_target, "Request accepted, but I could not create a private request channel. Delivery will appear in the upload channel."


async def create_dev_help_channel(ctx, source_channel, request_id):
    if not ctx.guild:
        return None
    category = discord.utils.get(ctx.guild.categories, name=REQUEST_CATEGORY_NAME) or getattr(source_channel, "category", None)
    name = f"help-{channel_safe_name(ctx.author.display_name)}"
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
    }
    for role in help_roles(ctx.guild):
        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    for member in await help_members(ctx.guild):
        overwrites[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    try:
        channel = await ctx.guild.create_text_channel(
            name=name,
            overwrites=overwrites,
            category=category,
            topic=f"Hash Slinging Downloader help channel for user {ctx.author.id}",
            reason=f"Help fallback channel for {request_id}",
        )
        await channel.send(
            f"Help requested for {source_channel.mention} by <@{ctx.author.id}>.\n"
            "The original request channel could not be opened directly, so this help channel was created for the dev team."
        )
        return channel
    except Exception:
        return None
