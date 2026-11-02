from __future__ import annotations

import logging

import discord
from discord import app_commands

from bot_app.automod import register_automod
from bot_app.branding import brand_embed
from bot_app.levels import register_levels
from bot_app.moderation import register_moderation
from bot_app.onboarding import register_onboarding
from bot_app.reaction_roles import register_reaction_roles
from bot_app.storage import BotStore
from bot_app.tickets import register_tickets

logger = logging.getLogger("discord_bot.commands")


def register_commands(bot: discord.Client, store: BotStore) -> None:
    register_onboarding(bot, store)
    register_automod(bot, store)
    register_moderation(bot)
    register_tickets(bot, store)
    register_reaction_roles(bot, store)
    register_levels(bot, store)

    @bot.tree.command(name="ping", description="Check NEXUS V1 latency.")
    @app_commands.guild_only()
    async def ping(interaction: discord.Interaction) -> None:
        latency_ms = round(bot.latency * 1000)
        await interaction.response.send_message(
            embed=brand_embed(
                "NEXUS V1 Online",
                f"Pong! **{latency_ms} ms**",
            )
        )

    @bot.tree.command(name="hello", description="Greetings from NEXUS V1.")
    @app_commands.guild_only()
    async def hello(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=brand_embed(
                "Welcome to NEXUS V1",
                f"Hello {interaction.user.mention}! Welcome to the future.",
            ),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )


async def handle_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        message = "You do not have permission to use that command."
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "This command can only be used inside a server."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = "That command is being used too quickly. Try again shortly."
    else:
        original = getattr(error, "original", error)
        command_name = (
            interaction.command.qualified_name
            if interaction.command is not None
            else "unknown"
        )
        logger.error(
            "Slash command %s failed with %s",
            command_name,
            type(original).__name__,
        )
        if isinstance(original, discord.Forbidden):
            message = (
                "I could not complete that action. Check my permissions and "
                "role position."
            )
        else:
            message = "That command failed. Check the bot's permissions and try again."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        logger.debug("Could not send slash-command error response.")
