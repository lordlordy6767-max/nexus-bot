from __future__ import annotations

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed


def register_server_info(bot: discord.Client) -> None:
    @bot.tree.command(name="userinfo", description="Show details about a server member.")
    @app_commands.guild_only()
    @app_commands.describe(user="Member whose details you want to view.")
    async def userinfo(
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        role_names = [role.name for role in reversed(user.roles) if not role.is_default()]
        role_text = ", ".join(role_names[:15]) or "No roles"
        if len(role_names) > 15:
            role_text += f", and {len(role_names) - 15} more"

        embed = brand_embed(
            f"User information · {user.display_name}",
            f"**Account ID:** `{user.id}`\n"
            f"**Created:** {discord.utils.format_dt(user.created_at, style='F')}\n"
            f"**Joined:** {discord.utils.format_dt(user.joined_at, style='F') if user.joined_at else 'Unknown'}\n"
            f"**Bot account:** {'Yes' if user.bot else 'No'}",
            color=PURPLE,
        )
        embed.add_field(name="Roles", value=role_text[:1024], inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="serverinfo", description="Show details about this server.")
    @app_commands.guild_only()
    async def serverinfo(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return
        owner = f"<@{guild.owner_id}>" if guild.owner_id else "Unknown"
        member_count = guild.member_count or len(guild.members)
        text_count = len(guild.text_channels)
        voice_count = len(guild.voice_channels)
        forum_count = len(guild.forums)
        embed = brand_embed(
            f"Server information · {guild.name}",
            f"**Owner:** {owner}\n"
            f"**Created:** {discord.utils.format_dt(guild.created_at, style='F')}\n"
            f"**Members:** {member_count:,}\n"
            f"**Roles:** {max(0, len(guild.roles) - 1)}\n"
            f"**Channels:** {text_count} text · {voice_count} voice · "
            f"{forum_count} forum\n"
            f"**Boosts:** {guild.premium_subscription_count or 0}",
            color=PURPLE,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="avatar", description="Show a user's avatar.")
    @app_commands.guild_only()
    @app_commands.describe(user="User whose avatar you want to view.")
    async def avatar(
        interaction: discord.Interaction,
        user: discord.User,
    ) -> None:
        avatar_url = user.display_avatar.url
        embed = brand_embed(
            f"{user.display_name}'s avatar",
            f"[Open full-size avatar]({avatar_url})",
            color=PURPLE,
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed)
