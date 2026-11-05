from __future__ import annotations

import logging

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.reaction_roles")

def register_reaction_roles(bot: discord.Client, store: BotStore) -> None:
    # --- KEEP YOUR OLD SINGLE COMMAND ---
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
        bot_member = guild.get_member(bot.user.id) if bot.user else None
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "I need the Manage Roles permission to assign reaction roles.",
                ephemeral=True,
            )
            return
        if role.is_default() or role.managed or not role.is_assignable():
            await interaction.response.send_message(
                "That role cannot be assigned by the bot. Choose a regular role below the bot's highest role.",
                ephemeral=True,
            )
            return

        parsed_emoji = discord.PartialEmoji.from_str(emoji.strip())
        if not parsed_emoji.name:
            await interaction.response.send_message("Enter a valid Unicode emoji or custom emoji.", ephemeral=True)
            return

        embed = brand_embed(
            "NEXUS V1 Reaction Role",
            f"React with {parsed_emoji} to receive {role.mention}.\nRemove your reaction to remove the role.",
            color=PURPLE,
        )
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            panel = await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            await panel.add_reaction(parsed_emoji)
        except discord.Forbidden:
            await interaction.followup.send("I could not post the panel. Check my permissions.", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send("Discord rejected that emoji.", ephemeral=True)
            return

        await store.set_reaction_role(panel.id, str(parsed_emoji), guild.id, role.id)
        await interaction.followup.send(f"Reaction role panel posted in {channel.mention}.", ephemeral=True)

    # --- NEW V2 MULTI COMMAND - 10 ROLES ---
    @bot.tree.command(
        name="reaction-roles-setup",
        description="Post ONE panel with up to 10 reaction roles (Multi).",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        channel="Where to post the panel",
        title="Title for the panel, e.g. Pick your roles!",
        role_1="First role", emoji_1="First emoji",
        role_2="Second role (optional)", emoji_2="Second emoji (optional)",
        role_3="Third role (optional)", emoji_3="Third emoji (optional)",
        role_4="Fourth role (optional)", emoji_4="Fourth emoji (optional)",
        role_5="Fifth role (optional)", emoji_5="Fifth emoji (optional)",
        role_6="Sixth role (optional)", emoji_6="Sixth emoji (optional)",
        role_7="Seventh role (optional)", emoji_7="Seventh emoji (optional)",
        role_8="Eighth role (optional)", emoji_8="Eighth emoji (optional)",
        role_9="Ninth role (optional)", emoji_9="Ninth emoji (optional)",
        role_10="Tenth role (optional)", emoji_10="Tenth emoji (optional)",
    )
    async def reaction_roles_setup(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        role_1: discord.Role, emoji_1: str,
        role_2: discord.Role | None = None, emoji_2: str | None = None,
        role_3: discord.Role | None = None, emoji_3: str | None = None,
        role_4: discord.Role | None = None, emoji_4: str | None = None,
        role_5: discord.Role | None = None, emoji_5: str | None = None,
        role_6: discord.Role | None = None, emoji_6: str | None = None,
        role_7: discord.Role | None = None, emoji_7: str | None = None,
        role_8: discord.Role | None = None, emoji_8: str | None = None,
        role_9: discord.Role | None = None, emoji_9: str | None = None,
        role_10: discord.Role | None = None, emoji_10: str | None = None,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        bot_member = guild.get_member(bot.user.id) if bot.user else None
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message("I need Manage Roles permission.", ephemeral=True)
            return

        pairs = [(role_1, emoji_1), (role_2, emoji_2), (role_3, emoji_3), (role_4, emoji_4), (role_5, emoji_5),
                 (role_6, emoji_6), (role_7, emoji_7), (role_8, emoji_8), (role_9, emoji_9), (role_10, emoji_10)]
        valid = []
        seen_emoji = set()
        for role, emoji_str in pairs:
            if role is None or emoji_str is None:
                continue
            if role.is_default() or role.managed or not role.is_assignable():
                await interaction.response.send_message(f"Role {role.mention} cannot be assigned by bot.", ephemeral=True)
                return
            parsed = discord.PartialEmoji.from_str(emoji_str.strip())
            if not parsed.name or str(parsed) in seen_emoji:
                await interaction.response.send_message(f"Invalid or duplicate emoji: {emoji_str}", ephemeral=True)
                return
            seen_emoji.add(str(parsed))
            valid.append((role, parsed))

        if not valid:
            await interaction.response.send_message("Add at least 1 role + emoji.", ephemeral=True)
            return

        lines = "\n".join([f"{emoji} - {role.mention}" for role, emoji in valid])
        embed = brand_embed(
            f"NEXUS V1 - {title}",
            f"{lines}\n\nReact to get a role. Remove your reaction to remove it.",
            color=PURPLE,
        )
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            panel = await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            for _, parsed in valid:
                await panel.add_reaction(parsed)
        except discord.Forbidden:
            await interaction.followup.send("I could not post panel. Check permissions.", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send("Discord rejected one of those emojis.", ephemeral=True)
            return

        for role, parsed in valid:
            await store.set_reaction_role(panel.id, str(parsed), guild.id, role.id)

        await interaction.followup.send(f"Multi reaction panel posted in {channel.mention} with {len(valid)} roles!", ephemeral=True)

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

    mapping = await store.get_reaction_role(payload.message_id, str(payload.emoji))
    if mapping is None or int(mapping["guild_id"]) != payload.guild_id:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    role = guild.get_role(int(mapping["role_id"]))
    bot_member = guild.get_member(bot.user.id)
    if role is None or bot_member is None or not bot_member.guild_permissions.manage_roles or not role.is_assignable():
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
        logger.warning("Cannot update reaction role %s for member %s", role.id, member.id)
    except discord.HTTPException:
        logger.warning("Discord rejected reaction role update for role %s", role.id)