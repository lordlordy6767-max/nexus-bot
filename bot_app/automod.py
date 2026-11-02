from __future__ import annotations

import datetime
import logging
import re
import time
from collections import defaultdict, deque

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.moderation_log import send_moderation_log
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.automod")
_recent_messages: dict[tuple[int, int], deque[float]] = defaultdict(deque)
_INVITE_PATTERN = re.compile(
    r"(?:discord\.gg/|discord(?:app)?\.com/invite/)",
    re.IGNORECASE,
)
_SPAM_WINDOW_SECONDS = 8
_last_prune = 0.0


def register_automod(bot: discord.Client, store: BotStore) -> None:
    group = app_commands.Group(
        name="automod",
        description="Configure NEXUS V1 automatic moderation.",
    )

    @group.command(name="configure", description="Set AutoMod rules.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        enabled="Turn automatic moderation on or off.",
        block_invites="Delete Discord invite links.",
        max_mentions="Maximum users or roles mentioned in one message.",
        spam_limit="Messages in eight seconds that trigger flood handling.",
    )
    async def configure(
        interaction: discord.Interaction,
        enabled: bool,
        block_invites: bool,
        max_mentions: app_commands.Range[int, 1, 20],
        spam_limit: app_commands.Range[int, 3, 20],
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        await store.set_settings(
            guild.id,
            automod_enabled=enabled,
            automod_block_invites=block_invites,
            automod_max_mentions=int(max_mentions),
            automod_spam_limit=int(spam_limit),
        )
        state = "enabled" if enabled else "disabled"
        await interaction.response.send_message(
            f"AutoMod is {state}. Invite blocking: "
            f"{'on' if block_invites else 'off'}; mention limit: "
            f"{max_mentions}; flood limit: {spam_limit} messages per "
            f"{_SPAM_WINDOW_SECONDS} seconds.",
            ephemeral=True,
        )

    @group.command(name="status", description="Show the current AutoMod rules.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def status(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return
        settings = await store.get_settings(guild.id)
        embed = brand_embed(
            "NEXUS V1 AutoMod",
            f"Status: **{'Enabled' if settings['automod_enabled'] else 'Disabled'}**\n"
            f"Block invite links: **{'Yes' if settings['automod_block_invites'] else 'No'}**\n"
            f"Mention limit: **{settings['automod_max_mentions']}**\n"
            f"Flood limit: **{settings['automod_spam_limit']} messages / "
            f"{_SPAM_WINDOW_SECONDS} seconds**",
            color=PURPLE,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    bot.tree.add_command(group)


async def handle_automod(store: BotStore, message: discord.Message) -> bool:
    global _last_prune
    guild = message.guild
    member = message.author
    if guild is None or not isinstance(member, discord.Member) or member.bot:
        return False

    settings = await store.get_settings(guild.id)
    if not settings["automod_enabled"] or member.guild_permissions.manage_messages:
        return False

    now = time.monotonic()
    if now - _last_prune > 60:
        for stale_key, timestamps in list(_recent_messages.items()):
            while timestamps and now - timestamps[0] > _SPAM_WINDOW_SECONDS:
                timestamps.popleft()
            if not timestamps:
                _recent_messages.pop(stale_key, None)
        _last_prune = now

    key = (guild.id, member.id)
    recent = _recent_messages[key]
    while recent and now - recent[0] > _SPAM_WINDOW_SECONDS:
        recent.popleft()
    recent.append(now)

    violation: str | None = None
    if (
        settings["automod_block_invites"]
        and _INVITE_PATTERN.search(message.content)
    ):
        violation = "Discord invite links are not allowed."

    mention_count = (
        len(message.mentions)
        + len(message.role_mentions)
        + (5 if message.mention_everyone else 0)
    )
    if violation is None and mention_count > int(settings["automod_max_mentions"]):
        violation = "That message mentioned too many members or roles."

    flood_detected = (
        violation is None
        and len(recent) >= int(settings["automod_spam_limit"])
    )
    if violation is None and flood_detected:
        violation = "Please slow down; the message flood was removed."

    if violation is None:
        return False

    if flood_detected:
        recent.clear()
    message_removed = True
    try:
        await message.delete()
    except discord.NotFound:
        pass
    except discord.Forbidden:
        logger.warning(
            "AutoMod could not delete a message in guild %s channel %s",
            guild.id,
            message.channel.id,
        )
        message_removed = False
    except discord.HTTPException:
        logger.exception(
            "AutoMod could not delete a message in guild %s channel %s",
            guild.id,
            message.channel.id,
        )
        message_removed = False

    timeout_applied = False
    if flood_detected:
        bot_member = guild.me
        if (
            bot_member is not None
            and bot_member.guild_permissions.moderate_members
            and member.id != guild.owner_id
            and member.top_role < bot_member.top_role
        ):
            try:
                await member.timeout(
                    discord.utils.utcnow() + datetime.timedelta(seconds=30),
                    reason="NEXUS V1 AutoMod: message flood",
                )
                timeout_applied = True
            except (discord.Forbidden, discord.HTTPException):
                logger.info(
                    "AutoMod removed a flood but could not timeout member %s",
                    member.id,
                )

    action = (
        "Removed violating message"
        if message_removed
        else "Could not remove violating message"
    )
    if flood_detected:
        action += (
            " and applied a 30-second timeout"
            if timeout_applied
            else "; timeout was not applied"
        )
    log_warning = await send_moderation_log(
        store,
        guild,
        action=action,
        actor="NEXUS V1 AutoMod",
        affected=member,
        reason=violation,
        occurred_at=message.created_at,
    )
    if log_warning:
        logger.warning(
            "AutoMod enforcement in guild %s was not recorded: %s",
            guild.id,
            log_warning,
        )

    try:
        await message.channel.send(
            embed=brand_embed(
                "NEXUS V1 AutoMod",
                f"{member.mention} {violation}",
                color=PURPLE,
            ),
            delete_after=8,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )
    except (discord.Forbidden, discord.HTTPException):
        logger.debug("AutoMod notice could not be sent in guild %s", guild.id)
    return True
