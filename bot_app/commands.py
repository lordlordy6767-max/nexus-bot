
from __future__ import annotations

import logging
import random

import discord
from discord import app_commands

from bot_app.automod import register_automod
from bot_app.antinuke import register_antinuke
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
        register_antinuke(bot)

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
        guild_obj = interaction.guild or (await interaction.client.fetch_guild(interaction.guild_id) if interaction.guild_id else None)
        guild_name = guild_obj.name if guild_obj and guild_obj.name else "this server"
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

    # ===== NEW COMMANDS =====

    @bot.tree.command(name="poll", description="Create a Yes / No poll.")
    @app_commands.describe(question="What are we voting on?")
    async def poll(interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(
            embed=brand_embed("📊 POLL 📊", f"**{question}**\n\n👍 = Yes\n👎 = No\n\nStarted by {interaction.user.mention}")
        )
        try:
            msg = await interaction.original_response()
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        except Exception as e:
            print(f"POLL REACTION ERROR: {e}")

    @bot.tree.command(name="8ball", description="Ask the Magic 8-Ball a question.")
    @app_commands.describe(question="What do you want to ask?")
    async def eightball(interaction: discord.Interaction, question: str) -> None:
        answers = [
            "Yes, definitely! ✅", "Nope, not a chance. ❌", "Maybe... ask again later. 🤔",
            "100% YES! 🔥", "My sources say no. 🙅", "Absolutely! Go for it! 🚀",
            "Don't count on it. 😬", "Signs point to yes. 👀", "Ask again, I'm sleeping. 😴",
            "Bro... yes. 💯", "Nah fam. 🚫", "In your dreams. 💭",
        ]
        await interaction.response.send_message(
            embed=brand_embed("🎱 Magic 8-Ball 🎱", f"**Question:** {question}\n\n**Answer:** {random.choice(answers)}\n\nAsked by {interaction.user.mention}")
        )

    @bot.tree.command(name="roast", description="Friendly roast someone.")
    @app_commands.describe(user="Who should I roast?")
    async def roast(interaction: discord.Interaction, user: discord.User) -> None:
        roasts = [
            "Your WiFi is faster than your brain. 📶",
            "You bring everyone so much joy... when you leave the room. 😂",
            "You're the reason we have loading screens. ⏳",
            "Your gameplay is so bad, even the bots feel sorry for you. 🤖",
            "You have the charisma of a buffering video. 🐢",
            "If laziness was an Olympic sport, you'd win gold while napping. 🥇😴",
            "You're proof that even Discord has a mute button for a reason. 🔇",
            "Your IQ and your ping have one thing in common... both are unstable. 📉",
        ]
        await interaction.response.send_message(
            embed=brand_embed("🔥 ROAST TIME 🔥", f"{user.mention}, {random.choice(roasts)}"),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )

    @bot.tree.command(name="announce", description="Post a fancy announcement. Staff only.")
    @app_commands.describe(title="Announcement title", message="What do you want to announce?", channel="Where to post it? (leave empty for this channel)")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def announce(interaction: discord.Interaction, title: str, message: str, channel: discord.TextChannel | None = None) -> None:
        await interaction.response.defer(ephemeral=True)
        target = channel or interaction.channel
        try:
            await target.send(embed=brand_embed(f"📢 {title} 📢", f"{message}\n\n— Posted by {interaction.user.mention}"))
            await interaction.followup.send(f"Announcement sent to {target.mention}! ✅", ephemeral=True)
        except Exception as e:
            print(f"ANNOUNCE ERROR: {e}")
            await interaction.followup.send(f"Couldn't announce there: {e}", ephemeral=True)

    @bot.tree.command(name="warn", description="Warn a member. Staff only.")
    @app_commands.describe(user="Who to warn?", reason="Why are they being warned?")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warn(interaction: discord.Interaction, user: discord.Member, reason: str) -> None:
        await interaction.response.send_message(
            embed=brand_embed("⚠️ WARNING ⚠️", f"{user.mention} has been warned.\n\n**Reason:** {reason}\n**By:** {interaction.user.mention}"),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        try:
            await user.send(f"⚠️ You were warned in **{interaction.guild.name}**:\n\n> {reason}")
        except Exception:
            pass

    @bot.tree.command(name="unmute", description="Unmute a member. Staff only.")
    @app_commands.describe(user="Who to unmute?")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def unmute(interaction: discord.Interaction, user: discord.Member) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await user.timeout(None)
            await interaction.followup.send(f"Unmuted {user.mention}! ✅", ephemeral=True)
        except Exception as e:
            print(f"UNMUTE ERROR: {e}")
            await interaction.followup.send(f"Couldn't unmute: {e}", ephemeral=True)

    @bot.tree.command(name="unban", description="Unban a user by ID. Staff only.")
    @app_commands.describe(user_id="The Discord ID of the banned user (right-click > Copy ID)")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.guild_only()
    async def unban(interaction: discord.Interaction, user_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            user_obj = await bot.fetch_user(int(user_id))
            await interaction.guild.unban(user_obj)
            await interaction.followup.send(f"Unbanned {user_obj.mention}! ✅", ephemeral=True)
        except Exception as e:
            print(f"UNBAN ERROR: {e}")
            await interaction.followup.send(f"Couldn't unban: {e}\nMake sure you copied the correct User ID.", ephemeral=True)

    @bot.tree.command(name="help", description="See all NEXUS commands.")
    async def help_cmd(interaction: discord.Interaction) -> None:
        text = (
            "**👋 Welcome / Fun**\n"
            "`/hello` `/greet` `/goodmorning` `/goodnight` `/shoutout` `/roast` `/8ball`\n\n"
            "**📊 Community**\n"
            "`/poll` `/rank` `/leaderboard`\n\n"
            "**📢 Staff**\n"
            "`/send` `/dm` `/announce` `/warn` `/ban` `/kick` `/mute` `/unmute` `/unban` `/clear`\n\n"
            "**⚙️ Setup / System**\n"
            "`/ping` `/verify` `/ticket-setup` `/reaction-role-setup` `/welcome set` `/list-roles` `/automod`\n\n"
            "**Tip:** Use `/poll` to vote, `/roast` to have fun, `/announce` for big news!"
        )
        await interaction.response.send_message(
            embed=brand_embed("🤖 NEXUS V1 - All Commands", text),
            ephemeral=True
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