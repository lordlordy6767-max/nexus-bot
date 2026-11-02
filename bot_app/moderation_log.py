from __future__ import annotations

import datetime
import logging
from typing import Any

import discord

from bot_app.branding import PURPLE, brand_embed
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.moderation_log")

_NOT_CONFIGURED = (
    "No moderation log channel is configured. An admin can run "
    "`/moderation-log set` with a private text channel."
)
_CHANNEL_UNAVAILABLE = (
    "The configured moderation log channel is missing or inaccessible. "
    "An admin should run `/moderation-log set` again."
)


def _subject(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, str):
        return value[:1024]
    mention = getattr(value, "mention", None)
    user_id = getattr(value, "id", None)
    label = str(value)
    if mention and user_id is not None:
        return f"{mention} ({label}, ID: {user_id})"[:1024]
    return label[:1024]


async def send_moderation_log(
    store: BotStore,
    guild: discord.Guild,
    *,
    action: str,
    actor: Any,
    affected: Any,
    reason: str,
    occurred_at: datetime.datetime | None = None,
) -> str | None:
    """Send an audit embed, returning an admin-facing warning on failure."""
    try:
        settings = await store.get_settings(guild.id)
        channel_id = settings.get("moderation_log_channel_id")
        if not channel_id:
            logger.warning(
                "Moderation event in guild %s was not logged: "
                "no log channel is configured.",
                guild.id,
            )
            return _NOT_CONFIGURED

        channel = guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            logger.warning(
                "Moderation event in guild %s was not logged: channel %s is missing or inaccessible.",
                guild.id,
                channel_id,
            )
            return _CHANNEL_UNAVAILABLE

        timestamp = occurred_at or discord.utils.utcnow()
        embed = brand_embed(
            f"Moderation • {action[:200]}",
            color=PURPLE,
        )
        embed.add_field(
            name="Actor",
            value=_subject(actor),
            inline=False,
        )
        embed.add_field(
            name="Affected member",
            value=_subject(affected),
            inline=False,
        )
        embed.add_field(
            name="Reason",
            value=(reason or "No reason provided")[:1024],
            inline=False,
        )
        embed.add_field(
            name="Timestamp",
            value=discord.utils.format_dt(timestamp, style="F"),
            inline=False,
        )
        embed.timestamp = timestamp
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return None
    except Exception:
        logger.exception(
            "Moderation event %r in guild %s could not be written to its log channel.",
            action,
            guild.id,
        )
        return _CHANNEL_UNAVAILABLE
