import discord

from helpers.request_state import help_requested, mark_help_requested


ADMIN_CHANNEL_NAME = "admin-commands-hsd"
ADMIN_ROLES = ("Dev and Maintainer", "Founders")
HELP_ROLES = ("Dev and Maintainer",)


def admin_roles(guild):
    if not guild:
        return []
    return [role for role in guild.roles if role.name in ADMIN_ROLES]


def admin_role_mentions(guild):
    roles = admin_roles(guild)
    return " ".join(role.mention for role in roles) if roles else ""


def help_roles(guild):
    if not guild:
        return []
    return [role for role in guild.roles if role.name in HELP_ROLES]


def help_role_mentions(guild):
    roles = help_roles(guild)
    return " ".join(role.mention for role in roles) if roles else ""


def is_help_role_member(member):
    role_names = {role.name for role in getattr(member, "roles", [])}
    return bool(role_names.intersection(HELP_ROLES))


async def help_members(guild):
    if not guild:
        return []
    members = []
    seen = set()
    for role in help_roles(guild):
        for member in getattr(role, "members", []):
            if member.id not in seen:
                seen.add(member.id)
                members.append(member)
    if members:
        return members
    try:
        async for member in guild.fetch_members(limit=None):
            if any(role.name in HELP_ROLES for role in getattr(member, "roles", [])) and member.id not in seen:
                seen.add(member.id)
                members.append(member)
    except Exception:
        pass
    return members


def has_admin_role(member):
    role_names = {role.name for role in getattr(member, "roles", [])}
    return bool(role_names.intersection(ADMIN_ROLES))


def is_admin_channel(channel):
    return getattr(channel, "name", None) == ADMIN_CHANNEL_NAME


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
        return False, ["not_text_channel"]
    granted = False
    errors = []
    for role in help_roles(channel.guild):
        try:
            await channel.set_permissions(
                role,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason="Requester asked for help in private download channel",
            )
            granted = True
        except Exception as exc:
            errors.append(f"{role.name}: {type(exc).__name__}")
    if granted:
        return granted, errors

    members = await help_members(channel.guild)
    for member in members:
        try:
            await channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                reason="Requester asked for help in private download channel",
            )
            granted = True
        except Exception as exc:
            errors.append(f"{member.display_name}: {type(exc).__name__}")
    return granted, errors


async def grant_dev_access(channel):
    return await grant_admin_access(channel)


async def ensure_requester_access(channel, member):
    if not isinstance(channel, discord.TextChannel) or member is None:
        return False
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            reason="Requester asked for help in private download channel",
        )
        return True
    except Exception:
        return False


async def grant_member_access(channel, member):
    if not isinstance(channel, discord.TextChannel) or member is None:
        return False
    try:
        await channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            reason="Dev joined a private request channel",
        )
        return True
    except Exception:
        return False


class HelpRequestView(discord.ui.View):
    def __init__(self, source_channel_id, requester_id):
        super().__init__(timeout=7200)
        self.source_channel_id = source_channel_id
        self.requester_id = requester_id

    async def _get_source_channel(self, interaction):
        if not interaction.guild:
            return None
        channel = interaction.guild.get_channel(self.source_channel_id)
        if channel is not None:
            return channel
        try:
            return await interaction.guild.fetch_channel(self.source_channel_id)
        except Exception:
            return None

    @discord.ui.button(label="Join channel", style=discord.ButtonStyle.green)
    async def join_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not is_help_role_member(interaction.user):
            await interaction.response.send_message("This button is for dev team members only.", ephemeral=True)
            return
        channel = await self._get_source_channel(interaction)
        if channel is None:
            await interaction.response.send_message("I could not find the request channel anymore.", ephemeral=True)
            return
        already_open = channel.permissions_for(interaction.user).view_channel
        granted = already_open or await grant_member_access(channel, interaction.user)
        if not granted:
            await interaction.response.send_message("I could not open the request channel for you.", ephemeral=True)
            return
        try:
            admin_channel = await get_admin_channel(interaction.guild)
            if admin_channel:
                if already_open:
                    await admin_channel.send(f"{interaction.user.mention} is already in {channel.mention}.")
                else:
                    await admin_channel.send(f"{interaction.user.mention} joined {channel.mention}.")
        except Exception:
            pass
        open_view = discord.ui.View()
        open_view.add_item(discord.ui.Button(label="Open request channel", style=discord.ButtonStyle.link, url=channel.jump_url))
        await interaction.response.send_message(
            f"You now have access to {channel.mention}. Use the button below to jump there right away.",
            view=open_view,
            ephemeral=True,
        )

    @discord.ui.button(label="Ignore", style=discord.ButtonStyle.gray)
    async def ignore_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not is_help_role_member(interaction.user):
            await interaction.response.send_message("This button is for dev team members only.", ephemeral=True)
            return
        await interaction.response.send_message("Okay, no changes made.", ephemeral=True)


class HelpButtonView(discord.ui.View):
    def __init__(self, source_channel_id, requester_id):
        super().__init__(timeout=7200)
        self.source_channel_id = source_channel_id
        self.requester_id = requester_id

    async def _get_source_channel(self, interaction):
        if not interaction.guild:
            return None
        channel = interaction.guild.get_channel(self.source_channel_id)
        if channel is not None:
            return channel
        try:
            return await interaction.guild.fetch_channel(self.source_channel_id)
        except Exception:
            return None

    @discord.ui.button(label="Request dev help", style=discord.ButtonStyle.blurple)
    async def request_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("Only the requester can use this button.", ephemeral=True)
            return
        if help_requested(self.source_channel_id):
            await interaction.response.send_message("Help was already requested for this channel.", ephemeral=True)
            return
        channel = await self._get_source_channel(interaction)
        if channel is None:
            await interaction.response.send_message("I could not find the request channel anymore.", ephemeral=True)
            return
        mark_help_requested(self.source_channel_id)
        posted = await post_help_request_notice(interaction.guild, channel, interaction.user)
        if posted:
            for item in self.children:
                item.disabled = True
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass
            await interaction.response.send_message("The dev team has been notified.", ephemeral=True)
        else:
            await interaction.response.send_message("I could not notify the dev team.", ephemeral=True)


async def post_help_request_notice(guild, source_channel, requester):
    if not guild:
        return False
    admin_channel = await get_admin_channel(guild)
    if admin_channel is None:
        return False
    view = HelpRequestView(source_channel.id, requester.id)
    mentions = help_role_mentions(guild)
    content = (
        f"{mentions} Help requested in {source_channel.mention} by {requester.mention}.\n"
        "Click **Join channel** if you want into the request, or **Ignore** to leave it private."
    )
    await admin_channel.send(
        content,
        view=view,
        allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
    )
    return True


async def notify_help_roles(channel, requester):
    members = await help_members(channel.guild)
    if members:
        mentions = " ".join(member.mention for member in members)
        await channel.send(
            f"{mentions} Help requested in {channel.mention} by <@{requester.id}>.",
            allowed_mentions=discord.AllowedMentions(roles=False, users=True, everyone=False),
        )
        return True
    roles = help_roles(channel.guild)
    if not roles:
        return False
    mentions = " ".join(role.mention for role in roles)
    await channel.send(
        f"{mentions} Help requested in {channel.mention} by <@{requester.id}>.",
        allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
    )
    return True
