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

    @bot.tree.command(name="send", description="Make NEXUS send a message for you.")
    async def send(interaction: discord.Interaction, message: str, channel: discord.TextChannel | None = None) -> None:
        await interaction.response.defer(ephemeral=True)
        target = channel or interaction.channel
        try:
            await target.send(message)
            await interaction.followup.send(f"Sent to {target.mention}! ✅", ephemeral=True)
        except Exception as e:
            print(f"SEND ERROR by {interaction.user}: {e}")
            await interaction.followup.send(f"Couldn't send there: {e}", ephemeral=True)

    @bot.tree.command(name="greet", description="Make NEXUS greet someone.")
    @app_commands.describe(user="Who should I greet?")
    async def greet(interaction: discord.Interaction, user: discord.User) -> None:
                guild = interaction.guild
        guild_name = guild.name if guild and guild.name else "this server"
        print(f"GREET DEBUG guild={guild} name={guild_name!r}")
        try:
            await interaction.response.send_message(
                embed=brand_embed("Hello! 👋", f"Hey {user.mention}! Welcome to {guild_name}! 🎉 Great to see you here!"),
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        except Exception as e:
            print(f"GREET ERROR by {interaction.user}: {e}")
            try:
                msg = f"Hey {user.mention}! Welcome to {guild_name}! 🎉"
                if not interaction.response.is_done():
                    await interaction.response.send_message(msg)
                else:
                    await interaction.followup.send(msg)
            except Exception as e2:
                print(f"GREET FALLBACK ERROR: {e2}")

    @bot.tree.command(name="dm", description="Make NEXUS DM someone a secret message.")
    @app_commands.describe(user="Who to DM?", message="What should I tell them?")
    async def dm(interaction: discord.Interaction, user: discord.User, message: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            guild_name = interaction.guild.name if interaction.guild else "a DM"
            await user.send(f"💌 You got a message from **{interaction.user.display_name}** in **{guild_name}**:\n\n> {message}")
            await interaction.followup.send(f"DM sent to {user.mention}! 🤫", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(f"Couldn't DM {user.mention} - they have DMs closed.", ephemeral=True)
        except Exception as e:
            print(f"DM ERROR by {interaction.user}: {e}")
            await interaction.followup.send(f"Couldn't DM: {e}", ephemeral=True)

    @bot.tree.command(name="shoutout", description="Hype someone up!")
    @app_commands.describe(user="Who deserves a shoutout?", reason="Why are they awesome?")
    async def shoutout(interaction: discord.Interaction, user: discord.User, reason: str) -> None:
        try:
            await interaction.response.send_message(
                embed=brand_embed("🔥 SHOUTOUT! 🔥", f"EVERYONE GIVE IT UP FOR {user.mention}!\n\n**{reason}** 🎉"),
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        except Exception as e:
            print(f"SHOUTOUT ERROR by {interaction.user}: {e}")
            try:
                await interaction.response.send_message(f"EVERYONE GIVE IT UP FOR {user.mention}! **{reason}** 🎉")
            except Exception:
                await interaction.followup.send(f"Shoutout for {user.mention}!", ephemeral=True)

    @bot.tree.command(name="goodmorning", description="Send a good morning message.")
    async def goodmorning(interaction: discord.Interaction) -> None:
        try:
            await interaction.response.send_message(embed=brand_embed("☀️ Good Morning NEXUS!", f"Good morning everyone! {interaction.user.mention} says rise and shine! ☕ Have an amazing day! ✨"))
        except Exception as e:
            print(f"GOODMORNING ERROR: {e}")
            await interaction.response.send_message(f"Good morning everyone! {interaction.user.mention} says rise and shine! ☕")

    @bot.tree.command(name="goodnight", description="Send a good night message.")
    async def goodnight(interaction: discord.Interaction) -> None:
        try:
            await interaction.response.send_message(embed=brand_embed("🌙 Good Night NEXUS!", f"Good night everyone! {interaction.user.mention} says sweet dreams! 😴 See you tomorrow! 💤"))
        except Exception as e:
            print(f"GOODNIGHT ERROR: {e}")
            await interaction.response.send_message(f"Good night everyone! {interaction.user.mention} says sweet dreams! 😴")

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