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
            "✅ Mod logs will now go to " + channel.mention,
            ephemeral=True,
        )
        log_text = "Mod logs channel set to " + channel.mention + "\nBy: " + interaction.user.mention
        await _log(bot, interaction.guild, "📋 Mod Logs Set", log_text)

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
            reason=safe_reason + " | NEXUS V1 by " + str(interaction.user),
            delete_message_seconds=0,
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member banned",
                member.mention + " was banned.\nReason: " + safe_reason,
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + member.mention + " (" + str(member.id) + ")\n**By:** " + interaction.user.mention + "\n**Reason:** " + safe_reason
        await _log(bot, interaction.guild, "🔨 BAN", log_text)

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
        await member.kick(reason=safe_reason + " | NEXUS V1 by " + str(interaction.user))
        await interaction.followup.send(
            embed=brand_embed(
                "Member kicked",
                member.mention + " was removed.\nReason: " + safe_reason,
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + member.mention + " (" + str(member.id) + ")\n**By:** " + interaction.user.mention + "\n**Reason:** " + safe_reason
        await _log(bot, interaction.guild, "👢 KICK", log_text)

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
            reason="NEXUS V1 clear by " + str(interaction.user),
        )
        await interaction.followup.send(
            "Deleted " + str(len(deleted)) + " message(s).",
            ephemeral=True,
        )
        log_text = "**By:** " + interaction.user.mention + "\n**Channel:** " + channel.mention + "\n**Deleted:** " + str(len(deleted)) + " messages"
        await _log(bot, interaction.guild, "🧹 CLEAR", log_text)

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
            reason=safe_reason + " | NEXUS V1 by " + str(interaction.user),
        )
        await interaction.followup.send(
            embed=brand_embed(
                "Member timed out",
                member.mention + " was timed out for " + str(minutes) + " minute(s).\nReason: " + safe_reason,
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + member.mention + " (" + str(member.id) + ")\n**By:** " + interaction.user.mention + "\n**Duration:** " + str(minutes) + " minute(s)\n**Reason:** " + safe_reason
        await _log(bot, interaction.guild, "🔇 MUTE", log_text)

    @bot.tree.command(name="unmute", description="Remove timeout from a member.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        error = _target_error(interaction, member)
        if error:
            await _send_error(interaction, error)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await member.timeout(None, reason=reason + " | NEXUS V1 by " + str(interaction.user))
        await interaction.followup.send(
            embed=brand_embed("Member unmuted", member.mention + " was unmuted.\nReason: " + reason, color=PURPLE),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + member.mention + " (" + str(member.id) + ")\n**By:** " + interaction.user.mention + "\n**Reason:** " + reason
        await _log(bot, interaction.guild, "🔊 UNMUTE", log_text)

    @bot.tree.command(name="unban", description="Unban a user by ID.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "No reason provided",
    ) -> None:
        try:
            user = await bot.fetch_user(int(user_id))
        except Exception:
            await _send_error(interaction, "Invalid user ID.")
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await interaction.guild.unban(user, reason=reason + " | NEXUS V1 by " + str(interaction.user))
        except Exception:
            await interaction.followup.send("That user is not banned.", ephemeral=True)
            return
        await interaction.followup.send(
            embed=brand_embed("User unbanned", user.mention + " was unbanned.\nReason: " + reason, color=PURPLE),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + user.mention + " (" + str(user.id) + ")\n**By:** " + interaction.user.mention + "\n**Reason:** " + reason
        await _log(bot, interaction.guild, "✅ UNBAN", log_text)

    @bot.tree.command(name="warn", description="Warn a member.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        error = _target_error(interaction, member)
        if error:
            await _send_error(interaction, error)
            return
        await interaction.response.send_message(
            embed=brand_embed("Member warned", member.mention + " was warned.\nReason: " + reason, color=PURPLE),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        log_text = "**Target:** " + member.mention + " (" + str(member.id) + ")\n**By:** " + interaction.user.mention + "\n**Reason:** " + reason
        await _log(bot, interaction.guild, "⚠️ WARN", log_text)
        try:
            await member.send("You were warned in **" + interaction.guild.name + "**\nReason: " + reason)
        except Exception:
            pass

    @bot.tree.command(name="lock", description="Lock this channel.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(interaction: discord.Interaction) -> None:
        ch = interaction.channel
        if not isinstance(ch, discord.TextChannel):
            await _send_error(interaction, "Use this in a text channel.")
            return
        overwrite = ch.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await ch.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason="Locked by " + str(interaction.user),
        )
        await interaction.response.send_message("🔒 " + ch.mention + " locked.", ephemeral=True)
        log_text = "**Channel:** " + ch.mention + "\n**By:** " + interaction.user.mention
        await _log(bot, interaction.guild, "🔒 LOCK", log_text)

    @bot.tree.command(name="unlock", description="Unlock this channel.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(interaction: discord.Interaction) -> None:
        ch = interaction.channel
        if not isinstance(ch, discord.TextChannel):
            await _send_error(interaction, "Use this in a text channel.")
            return
        overwrite = ch.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await ch.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason="Unlocked by " + str(interaction.user),
        )
        await interaction.response.send_message("🔓 " + ch.mention + " unlocked.", ephemeral=True)
        log_text = "**Channel:** " + ch.mention + "\n**By:** " + interaction.user.mention
        await _log(bot, interaction.guild, "🔓 UNLOCK", log_text)

    if not getattr(bot, "_nexus_modlog_listeners", False):
        bot._nexus_modlog_listeners = True

        @bot.event
        async def on_message_delete(message: discord.Message):
            if message.guild is None or message.author.bot:
                return
            content = message.content[:1000] if message.content else "[no text / embed / attachment]"
            text = "**Author:** " + message.author.mention + " (" + str(message.author.id) + ")\n**Channel:** " + message.channel.mention + "\n**Content:** " + content
            await _log(bot, message.guild, "🗑️ MESSAGE DELETED", text)

        @bot.event
        async def on_message_edit(before: discord.Message, after: discord.Message):
            if before.guild is None or before.author.bot:
                return
            if before.content == after.content:
                return
            text = "**Author:** " + before.author.mention + " (" + str(before.author.id) + ")\n**Channel:** " + before.channel.mention + "\n**Before:** " + before.content[:500] + "\n**After:** " + after.content[:500] + "\nJump: " + after.jump_url
            await _log(bot, before.guild, "✏️ MESSAGE EDITED", text)