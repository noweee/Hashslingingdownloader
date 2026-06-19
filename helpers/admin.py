import discord


ADMIN_CHANNEL_NAME = "admin-commands-hsd"
ADMIN_ROLES = ("Dev and Maintainer", "Founders")


def admin_roles(guild):
    if not guild:
        return []
    return [role for role in guild.roles if role.name in ADMIN_ROLES]


def has_admin_role(member):
    role_names = {role.name for role in getattr(member, "roles", [])}
    return bool(role_names.intersection(ADMIN_ROLES))


async def get_admin_channel(guild):
    if not guild:
        return None
    existing = discord.utils.get(guild.text_channels, name=ADMIN_CHANNEL_NAME)
    if existing:
        return existing

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True),
    }
    for role in admin_roles(guild):
        overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    try:
        return await guild.create_text_channel(
            ADMIN_CHANNEL_NAME,
            overwrites=overwrites,
            reason="Hash Slinging Downloader admin command channel",
        )
    except Exception:
        return None


async def send_admin_output(ctx, **kwargs):
    channel = await get_admin_channel(ctx.guild)
    if channel:
        return await channel.send(**kwargs)
    return await ctx.reply(**kwargs)


async def grant_admin_access(channel):
    if not isinstance(channel, discord.TextChannel):
        return False
    granted = False
    for role in admin_roles(channel.guild):
        try:
            await channel.set_permissions(
                role,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason="Requester asked for help in private download channel",
            )
            granted = True
        except Exception:
            pass
    return granted
