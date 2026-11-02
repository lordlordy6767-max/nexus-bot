from __future__ import annotations

import logging

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.reaction_roles")


def register_reaction_roles(bot: discord.Client, store: BotStore) -> None:
    @bot.tree.command(
        name="reaction-role-setup",
        description="Post a reaction that assigns a server role.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reaction_role_setup(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role,
        emoji: str,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        actor = interaction.user
        bot_member = guild.get_member(bot.user.id) if bot.user else None
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "I need the Manage Roles permission to assign reaction roles.",
                ephemeral=True,
            )
            return
        if role.is_default() or role.managed or not role.is_assignable():
            await interaction.response.send_message(
                "That role cannot be assigned by the bot. Choose a regular role "
                "below the bot's highest role.",
                ephemeral=True,
            )
            return
        if (
            isinstance(actor, discord.Member)
            and actor.id != guild.owner_id
            and role >= actor.top_role
        ):
            await interaction.response.send_message(
                "Choose a role below your highest role.",
                ephemeral=True,
            )
            return

        parsed_emoji = discord.PartialEmoji.from_str(emoji.strip())
        if not parsed_emoji.name:
            await interaction.response.send_message(
                "Enter a valid Unicode emoji or custom emoji.",
                ephemeral=True,
            )
            return

        embed = brand_embed(
            "NEXUS V1 Reaction Role",
            f"React with {parsed_emoji} to receive {role.mention}.\n"
            "Remove your reaction to remove the role.",
            color=PURPLE,
        )
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            panel = await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await panel.add_reaction(parsed_emoji)
        except discord.Forbidden:
            await interaction.followup.send(
                "I could not post the panel or add its reaction. Check my "
                "View Channel, Send Messages, and Add Reactions permissions.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                "Discord rejected that emoji. Try a standard or server emoji.",
                ephemeral=True,
            )
            return

        await store.set_reaction_role(
            panel.id,
            str(parsed_emoji),
            guild.id,
            role.id,
        )
        await interaction.followup.send(
            f"Reaction role panel posted in {channel.mention}.",
            ephemeral=True,
        )


async def handle_reaction(
    bot: discord.Client,
    store: BotStore,
    payload: discord.RawReactionActionEvent,
    *,
    added: bool,
) -> None:
    if payload.guild_id is None or bot.user is None:
        return
    if payload.user_id == bot.user.id:
        return

    mapping = await store.get_reaction_role(
        payload.message_id,
        str(payload.emoji),
    )
    if mapping is None or int(mapping["guild_id"]) != payload.guild_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    role = guild.get_role(int(mapping["role_id"]))
    bot_member = guild.get_member(bot.user.id)
    if (
        role is None
        or bot_member is None
        or not bot_member.guild_permissions.manage_roles
        or not role.is_assignable()
    ):
        return

    member = payload.member
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
    if member.bot:
        return

    try:
        if added and role not in member.roles:
            await member.add_roles(role, reason="NEXUS V1 reaction role")
        elif not added and role in member.roles:
            await member.remove_roles(role, reason="NEXUS V1 reaction role removed")
    except discord.Forbidden:
        logger.warning(
            "Cannot update reaction role %s for member %s in guild %s",
            role.id,
            member.id,
            guild.id,
        )
    except discord.HTTPException:
        logger.warning(
            "Discord rejected reaction role update for role %s in guild %s",
            role.id,
            guild.id,
        )
