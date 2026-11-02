from __future__ import annotations

import discord
from discord import app_commands

from bot_app.storage import BotStore


def _permissions_error(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    *,
    edit_overwrites: bool,
) -> str | None:
    guild = interaction.guild
    actor = interaction.user
    if guild is None or not isinstance(actor, discord.Member):
        return "This command can only be used inside a server."
    actor_permissions = channel.permissions_for(actor)
    if not actor_permissions.manage_channels:
        return "You need Manage Channels permission in that channel."
    if edit_overwrites and not actor_permissions.manage_roles:
        return "You need Manage Roles permission to change channel access."

    bot_member = guild.me
    if bot_member is None:
        return "I could not verify my server permissions."
    bot_permissions = channel.permissions_for(bot_member)
    if not bot_permissions.manage_channels:
        return "I need Manage Channels permission in that channel."
    if edit_overwrites and not bot_permissions.manage_roles:
        return "I need Manage Roles permission to change channel access."
    return None


def register_channel_controls(
    bot: discord.Client,
    store: BotStore,
) -> None:
    @bot.tree.command(name="lock", description="Block @everyone from sending in a channel.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True, manage_roles=True)
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    @app_commands.describe(channel="Text channel to lock.")
    async def lock(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        error = _permissions_error(interaction, channel, edit_overwrites=True)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        settings = await store.get_settings(guild.id)
        lock_states = dict(settings.get("channel_lock_overwrites") or {})
        key = str(channel.id)
        if key in lock_states:
            await interaction.response.send_message(
                f"{channel.mention} is already locked by NEXUS V1.",
                ephemeral=True,
            )
            return

        overwrite = channel.overwrites_for(guild.default_role)
        if overwrite.send_messages is False:
            await interaction.response.send_message(
                f"{channel.mention} already blocks @everyone. "
                "I left the existing permission unchanged.",
                ephemeral=True,
            )
            return
        original_value = overwrite.send_messages
        lock_states[key] = original_value
        await store.set_settings(guild.id, channel_lock_overwrites=lock_states)

        overwrite.send_messages = False
        try:
            await channel.set_permissions(
                guild.default_role,
                overwrite=overwrite,
                reason=f"NEXUS V1 channel lock by {interaction.user}",
            )
        except discord.Forbidden:
            lock_states.pop(key, None)
            await store.set_settings(guild.id, channel_lock_overwrites=lock_states)
            await interaction.response.send_message(
                "I could not lock that channel. Check my Manage Channels and "
                "Manage Roles permissions.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Locked {channel.mention}. Use `/unlock` to restore its previous "
            "everyone permission.",
            ephemeral=True,
        )

    @bot.tree.command(name="unlock", description="Restore a NEXUS V1 channel lock.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True, manage_roles=True)
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    @app_commands.describe(channel="Text channel to unlock.")
    async def unlock(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        error = _permissions_error(interaction, channel, edit_overwrites=True)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        settings = await store.get_settings(guild.id)
        lock_states = dict(settings.get("channel_lock_overwrites") or {})
        key = str(channel.id)
        if key not in lock_states:
            await interaction.response.send_message(
                f"{channel.mention} has no saved NEXUS V1 lock. "
                "I left its current permissions unchanged.",
                ephemeral=True,
            )
            return
        original_value = lock_states[key]
        if original_value not in (None, True, False):
            await interaction.response.send_message(
                "The saved channel permission is invalid. Ask an administrator "
                "to review the bot database before unlocking.",
                ephemeral=True,
            )
            return

        overwrite = channel.overwrites_for(guild.default_role)
        overwrite.send_messages = original_value
        try:
            await channel.set_permissions(
                guild.default_role,
                overwrite=overwrite,
                reason=f"NEXUS V1 channel unlock by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I could not unlock that channel. Check my Manage Channels and "
                "Manage Roles permissions.",
                ephemeral=True,
            )
            return

        lock_states.pop(key, None)
        await store.set_settings(guild.id, channel_lock_overwrites=lock_states)
        await interaction.response.send_message(
            f"Unlocked {channel.mention} and restored its previous @everyone permission.",
            ephemeral=True,
        )

    @bot.tree.command(
        name="slowmode",
        description="Set slowmode in the current text channel.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode delay from 0 to 21600 seconds.")
    async def slowmode(
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600],
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Use this command in a server text channel.",
                ephemeral=True,
            )
            return
        error = _permissions_error(interaction, channel, edit_overwrites=False)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        await channel.edit(
            slowmode_delay=int(seconds),
            reason=f"NEXUS V1 slowmode set by {interaction.user}",
        )
        state = "disabled" if seconds == 0 else f"set to {seconds} second(s)"
        await interaction.response.send_message(
            f"Slowmode {state} in {channel.mention}.",
            ephemeral=True,
        )
