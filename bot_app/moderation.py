from __future__ import annotations

import datetime

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed

MODLOG_CHANNELS: dict[int, int] = {}

async def _log(guild: discord.Guild, embed: discord.Embed) -> None:
    channel_id = MODLOG_CHANNELS.get(guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        try:
            await channel.send(embed=embed)
        except Exception:
            pass


def _target_error(
    interaction: discord.Interaction,
    target: discord.Member,
) -> str | None:
    guild = interaction.guild
    actor = interaction.user
    if guild is None or not isinstance(actor, discord.Member):
        return "This command can only be used inside a server."
    if target.id == guild.owner_id:
        return "The server owner cannot be targeted."
    if target.id == actor.id:
        return "You cannot target yourself."
    client_user = interaction.client.user
    if target.bot and client_user is not None and target.id == client_user.id:
        return "I cannot target myself."
    if actor.id != guild.owner_id and target.top_role >= actor.top_role:
        return "You can only target members below your highest role."

    bot_member = guild.me
    if bot_member is None or target.top_role >= bot_member.top_role:
        return "The target is at or above my highest role. Move my role higher."
    return None


async def _send_error(
    interaction: discord.Interaction,
    message: str,
) -> None:
    await interaction.response.send_message(message, ephemeral=True)


def register_moderation(bot: discord.Client) -> None:
    @bot.tree.command(name="ban", description="Ban a member from this server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(reason="Reason recorded in the audit log.")
    async def ban(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        error = _target_error(interaction, member)
        if error:
            await _send_error(interaction, error)
            return
        bot_member = interaction.guild.me if interaction.guild is not None else None
        if bot_member is None or not bot_member.guild_permissions.ban_members:
            await _send_error(
                interaction,
                "I need the Ban Members permission to do that.",
            )
            return

        safe_reason = reason[:450]
        await interaction.response.defer(ephemeral=True, thinking=True)
        await member.ban(
            reason=f"{safe_reason} | NEXUS V1 by {interaction.user}",
            delete_message_seconds=0,
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member banned",
                f"{member.mention} was banned.\nReason: {safe_reason}",
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="kick", description="Remove a member from this server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(reason="Reason recorded in the audit log.")
    async def kick(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        error = _target_error(interaction, member)
        if error:
            await _send_error(interaction, error)
            return
        bot_member = interaction.guild.me if interaction.guild is not None else None
        if bot_member is None or not bot_member.guild_permissions.kick_members:
            await _send_error(
                interaction,
                "I need the Kick Members permission to do that.",
            )
            return

        safe_reason = reason[:450]
        await interaction.response.defer(ephemeral=True, thinking=True)
        await member.kick(reason=f"{safe_reason} | NEXUS V1 by {interaction.user}")
        await interaction.followup.send(
            embed=brand_embed(
                "Member kicked",
                f"{member.mention} was removed.\nReason: {safe_reason}",
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="clear", description="Delete recent messages.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100] = 10,
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            await _send_error(
                interaction,
                "Use this command in a text channel or thread.",
            )
            return
        bot_member = interaction.guild.me if interaction.guild is not None else None
        if bot_member is None or not bot_member.guild_permissions.manage_messages:
            await _send_error(
                interaction,
                "I need the Manage Messages permission to do that.",
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        deleted = await channel.purge(
            limit=int(amount),
            reason=f"NEXUS V1 clear by {interaction.user}",
        )
        await interaction.followup.send(
            f"Deleted {len(deleted)} message(s).",
            ephemeral=True,
        )

    @bot.tree.command(
        name="mute",
        description="Temporarily timeout a member.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: app_commands.Range[int, 1, 40320],
        reason: str = "No reason provided",
    ) -> None:
        error = _target_error(interaction, member)
        if error:
            await _send_error(interaction, error)
            return
        bot_member = interaction.guild.me if interaction.guild is not None else None
        if bot_member is None or not bot_member.guild_permissions.moderate_members:
            await _send_error(
                interaction,
                "I need the Moderate Members permission to do that.",
            )
            return

        safe_reason = reason[:450]
        until = discord.utils.utcnow() + datetime.timedelta(minutes=int(minutes))
        await interaction.response.defer(ephemeral=True, thinking=True)
        await member.timeout(
            until,
            reason=f"{safe_reason} | NEXUS V1 by {interaction.user}",
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member timed out",
                f"{member.mention} was timed out for {minutes} minute(s).\n"
                f"Reason: {safe_reason}",
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

