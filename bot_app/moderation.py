from __future__ import annotations

import datetime

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed

# ===== MOD LOGS STORAGE =====
# guild_id -> channel_id
_modlog_channels: dict[int, int] = {}

async def _log(bot: discord.Client, guild: discord.Guild | None, title: str, desc: str, color=PURPLE):
    if guild is None:
        return
    channel_id = _modlog_channels.get(guild.id)
    if not channel_id:
        return
    ch = guild.get_channel(channel_id)
    if not isinstance(ch, discord.TextChannel):
        return
    try:
        embed = brand_embed(title, desc, color=color)
        embed.timestamp = discord.utils.utcnow()
        await ch.send(embed=embed)
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
    @bot.tree.command(name="set-modlogs", description="Set where mod logs go.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_modlogs(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        _modlog_channels[interaction.guild.id] = channel.id
        await interaction.response.send_message(
            f"✅ Mod logs will now go to {channel.mention}",
            ephemeral=True,
        )
        await _log(bot, interaction.guild, "📋 Mod Logs Set", f"Mod logs channel set to {channel.mention}\nBy: {interaction.user.mention}")

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
        await _log(bot, interaction.guild, "🔨 BAN", f"**Target:** {member.mention} ({member.id})\n**By:** {interaction.user.mention}\n**Reason:** {safe_reason}")

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
                f"{member.mention} was removed