from __future__ import annotations

import datetime

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.moderation_log import send_moderation_log
from bot_app.storage import BotStore


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


def register_moderation(bot: discord.Client, store: BotStore) -> None:
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
        log_warning = await send_moderation_log(
            store,
            interaction.guild,
            action="Banned member",
            actor=interaction.user,
            affected=member,
            reason=safe_reason,
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member banned",
                f"{member.mention} was banned.\nReason: {safe_reason}"
                + (f"\n\nWarning: {log_warning}" if log_warning else ""),
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
        log_warning = await send_moderation_log(
            store,
            interaction.guild,
            action="Kicked member",
            actor=interaction.user,
            affected=member,
            reason=safe_reason,
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member kicked",
                f"{member.mention} was removed.\nReason: {safe_reason}"
                + (f"\n\nWarning: {log_warning}" if log_warning else ""),
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
        log_warning = await send_moderation_log(
            store,
            interaction.guild,
            action="Cleared messages",
            actor=interaction.user,
            affected=f"{len(deleted)} message(s) in #{channel.name}",
            reason=f"Bulk message clear; {len(deleted)} message(s) deleted.",
        )
        await interaction.followup.send(
            f"Deleted {len(deleted)} message(s)."
            + (f"\n\nWarning: {log_warning}" if log_warning else ""),
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
        log_warning = await send_moderation_log(
            store,
            interaction.guild,
            action=f"Timed out member for {minutes} minute(s)",
            actor=interaction.user,
            affected=member,
            reason=safe_reason,
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member timed out",
                f"{member.mention} was timed out for {minutes} minute(s).\n"
                f"Reason: {safe_reason}"
                + (f"\n\nWarning: {log_warning}" if log_warning else ""),
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    log_group = app_commands.Group(
        name="moderation-log",
        description="Configure the private moderation log channel.",
    )

    @log_group.command(name="set", description="Choose a private log channel.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(channel="Private text channel for moderation logs.")
    async def set_log_channel(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            await _send_error(
                interaction,
                "This command can only be used inside a server.",
            )
            return
        issue = _log_channel_issue(guild, channel)
        if issue:
            await _send_error(interaction, issue)
            return

        await store.set_settings(
            guild.id,
            moderation_log_channel_id=channel.id,
        )
        await interaction.response.send_message(
            f"Moderation events will be logged in {channel.mention}.",
            ephemeral=True,
        )

    @log_group.command(name="disable", description="Turn off moderation logging.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def disable_log_channel(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await _send_error(
                interaction,
                "This command can only be used inside a server.",
            )
            return
        await store.set_settings(guild.id, moderation_log_channel_id=None)
        await interaction.response.send_message(
            "Moderation logging is disabled.",
            ephemeral=True,
        )

    @log_group.command(name="status", description="Check moderation log delivery.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def log_status(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await _send_error(
                interaction,
                "This command can only be used inside a server.",
            )
            return

        settings = await store.get_settings(guild.id)
        channel_id = settings.get("moderation_log_channel_id")
        if not channel_id:
            message = (
                "Moderation logging is not configured. An admin can run "
                "`/moderation-log set` with a private text channel."
            )
        else:
            channel = guild.get_channel(int(channel_id))
            issue = (
                "The configured moderation log channel is missing or inaccessible."
                if not isinstance(channel, discord.TextChannel)
                else _log_channel_issue(guild, channel)
            )
            message = (
                f"Warning: {issue} Run `/moderation-log set` to choose a "
                "private channel."
                if issue
                else (
                    "Moderation logging is configured for "
                    f"{channel.mention}; permissions currently allow delivery."
                )
            )
        await interaction.response.send_message(message, ephemeral=True)

    bot.tree.add_command(log_group)


def _log_channel_issue(
    guild: discord.Guild,
    channel: discord.TextChannel,
) -> str | None:
    if channel.guild.id != guild.id:
        return "Choose a text channel from this server."
    if channel.permissions_for(guild.default_role).view_channel:
        return "The log channel must be private and hidden from @everyone."

    bot_member = guild.me
    if bot_member is None:
        return "I could not verify my channel permissions. Try again shortly."
    permissions = channel.permissions_for(bot_member)
    missing = [
        label
        for attribute, label in (
            ("view_channel", "View Channel"),
            ("send_messages", "Send Messages"),
            ("embed_links", "Embed Links"),
        )
        if not getattr(permissions, attribute, False)
    ]
    if missing:
        return (
            "I need these permissions in the log channel: "
            + ", ".join(missing)
            + "."
        )
    return None
