from __future__ import annotations

import logging

import discord
from discord import app_commands

from bot_app.branding import CYAN, brand_embed
from bot_app.storage import BotStore

logger = logging.getLogger("discord_bot.onboarding")


class VerifyView(discord.ui.View):
    def __init__(self, store: BotStore) -> None:
        super().__init__(timeout=None)
        self.store = store

    @discord.ui.button(
        label="VERIFY",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="nexus:verify",
    )
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Verification is only available inside a server.",
                ephemeral=True,
            )
            return

        settings = await self.store.get_settings(guild.id)
        role_id = settings.get("verified_role_id")
        role = guild.get_role(int(role_id)) if role_id else None
        if role is None:
            await interaction.response.send_message(
                "The verification role is not configured. Ask a server "
                "administrator to run `/verify` again.",
                ephemeral=True,
            )
            return
        if role in member.roles:
            await interaction.response.send_message(
                "You are already verified.",
                ephemeral=True,
            )
            return
        if not role.is_assignable():
            await interaction.response.send_message(
                "The bot cannot assign the VERIFIED role. Ask an administrator "
                "to move the bot role above VERIFIED.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await member.add_roles(role, reason="NEXUS V1 verification")
        except discord.Forbidden:
            await interaction.followup.send(
                "I could not assign the VERIFIED role. Check my Manage Roles "
                "permission and role position.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "Welcome to NEXUS V1! You are now verified.",
            ephemeral=True,
        )


def register_onboarding(bot: discord.Client, store: BotStore) -> None:
    tree = bot.tree
    welcome = app_commands.Group(
        name="welcome",
        description="Configure NEXUS V1 welcome messages.",
    )

    @tree.command(
        name="verify",
        description="Post the NEXUS V1 verification panel.",
    )
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_setup(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        channel = interaction.channel
        if guild is None or channel is None or not hasattr(channel, "send"):
            await interaction.response.send_message(
                "Run this command in a server text channel.",
                ephemeral=True,
            )
            return
        bot_member = guild.get_member(bot.user.id) if bot.user else None
        if bot_member is None or not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "I need the Manage Roles permission to configure verification.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        role = guild.get_role(
            int((await store.get_settings(guild.id)).get("verified_role_id") or 0)
        )
        if role is None:
            role = discord.utils.get(guild.roles, name="VERIFIED")
        try:
            if role is None:
                role = await guild.create_role(
                    name="VERIFIED",
                    colour=CYAN,
                    reason="NEXUS V1 verification setup",
                )
            if not role.is_assignable():
                await interaction.followup.send(
                    "Move the bot's role above VERIFIED, then run `/verify` again.",
                    ephemeral=True,
                )
                return
            await store.set_settings(guild.id, verified_role_id=role.id)
            await channel.send(
                embed=brand_embed(
                    "NEXUS V1 VERIFICATION",
                    "Welcome to the future.\n\n"
                    "Click the button below to verify and gain access "
                    "to the server.\n\n**Premium Security System**",
                ),
                view=VerifyView(store),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I could not create the verification role or post the panel. "
                "Check my Manage Roles and Send Messages permissions.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "Verification panel deployed.",
            ephemeral=True,
        )

    @welcome.command(name="set", description="Choose the welcome channel.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_set(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        await store.set_settings(guild.id, welcome_channel_id=channel.id)
        await interaction.response.send_message(
            f"Welcome messages will be sent to {channel.mention}.",
            ephemeral=True,
        )

    @welcome.command(name="disable", description="Turn off welcome messages.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_disable(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return
        await store.set_settings(guild.id, welcome_channel_id=None)
        await interaction.response.send_message(
            "Welcome messages are disabled.",
            ephemeral=True,
        )

    tree.add_command(welcome)


async def handle_member_join(
    store: BotStore,
    member: discord.Member,
) -> None:
    settings = await store.get_settings(member.guild.id)
    channel_id = settings.get("welcome_channel_id")
    channel = member.guild.get_channel(int(channel_id)) if channel_id else None
    if not isinstance(channel, discord.TextChannel):
        return

    embed = brand_embed(
        "Welcome to NEXUS V1",
        f"{member.mention} just joined the future!",
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    try:
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )
    except discord.Forbidden:
        logger.warning(
            "Cannot post a welcome message in guild %s channel %s",
            member.guild.id,
            channel.id,
        )
