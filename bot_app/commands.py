from __future__ import annotations

import logging
import random
import asyncio
import time

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

# ===== ECONOMY STORAGE (in-memory) =====
_balances = {}
_daily_claimed = {}
_giveaways = {}

def _get_bal(uid):
    return _balances.get(uid, 0)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="nexus_close_ticket_v2")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing ticket in 5 seconds... 🔒", ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"CLOSE TICKET ERROR: {e}")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, custom_id="nexus_ticket_v2")
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
        await ch.send(f"{interaction.user.mention} Ticket created! Staff will help you soon. Type your issue here.", view=CloseTicketView())
        await interaction.followup.send(f"Ticket created: {ch.mention} ✅", ephemeral=True)

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
        await interaction.response.send_message(embed=brand_embed("NEXUS V1 Online", f"Pong! **{latency_ms} ms**"))

    @bot.tree.command(name="hello", description="Greetings from NEXUS V1.")
    @app_commands.guild_only()
    async def hello(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=brand_embed("Welcome to NEXUS V1", f"Hello {interaction.user.mention}! Welcome to the future."), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))

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
            await interaction.response.send_message(embed=brand_embed("Hello! 👋", f"Hey {user.mention}! Welcome to {guild_name}! 🎉 Great to see you here!"), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
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
            await interaction.response.send_message(embed=brand_embed("🔥 SHOUTOUT! 🔥", f"EVERYONE GIVE IT UP FOR {user.mention}!\n\n**{reason}** 🎉"), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
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

    @bot.tree.command(name="poll", description="Create a Yes / No poll.")
    @app_commands.describe(question="What are we voting on?")
    async def poll(interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(embed=brand_embed("📊 POLL 📊", f"**{question}**\n\n👍 = Yes\n👎 = No\n\nStarted by {interaction.user.mention}"))
        try:
            msg = await interaction.original_response()
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        except Exception as e:
            print(f"POLL REACTION ERROR: {e}")

    @bot.tree.command(name="8ball", description="Ask the Magic 8-Ball a question.")
    @app_commands.describe(question="What do you want to ask?")
    async def eightball(interaction: discord.Interaction, question: str) -> None:
        answers = ["Yes, definitely! ✅", "Nope, not a chance. ❌", "Maybe... ask again later. 🤔", "100% YES! 🔥", "My sources say no. 🙅", "Absolutely! Go for it! 🚀", "Don't count on it. 😬", "Signs point to yes. 👀", "Ask again, I'm sleeping. 😴", "Bro... yes. 💯", "Nah fam. 🚫", "In your dreams. 💭"]
        await interaction.response.send_message(embed=brand_embed("🎱 Magic 8-Ball 🎱", f"**Question:** {question}\n\n**Answer:** {random.choice(answers)}\n\nAsked by {interaction.user.mention}"))

    @bot.tree.command(name="roast", description="Friendly roast someone.")
    @app_commands.describe(user="Who should I roast?")
    async def roast(interaction: discord.Interaction, user: discord.User) -> None:
        roasts = ["Your WiFi is faster than your brain. 📶", "You bring everyone so much joy... when you leave the room. 😂", "You're the reason we have loading screens. ⏳", "Your gameplay is so bad, even the bots feel sorry for you. 🤖", "You have the charisma of a buffering video. 🐢", "If laziness was an Olympic sport, you'd win gold while napping. 🥇😴", "You're proof that even Discord has a mute button for a reason. 🔇", "Your IQ and your ping have one thing in common... both are unstable. 📉"]
        await interaction.response.send_message(embed=brand_embed("🔥 ROAST TIME 🔥", f"{user.mention}, {random.choice(roasts)}"), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))

    @bot.tree.command(name="announce", description="Post a fancy announcement. Staff only.")
@app_commands.describe(title="Announcement title", message="What do you want to announce?", channel="Where to post it? (leave empty for this channel)", image="Optional image to attach to the announcement")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guild_only()
async def announce(interaction: discord.Interaction, title: str, message: str, channel: discord.TextChannel | None = None, image: discord.Attachment | None = None) -> None:
    await interaction.response.defer(ephemeral=True)
    target = channel or interaction.channel
    try:
        embed = brand_embed(f"📢 {title} 📢", f"{message}\n\n— Posted by {interaction.user.mention}")
        if image:
            # Only allow actual images
            if image.content_type and image.content_type.startswith("image/"):
                embed.set_image(url=image.url)
            else:
                await interaction.followup.send("That file wasn't an image, so I posted without it. ⚠️", ephemeral=True)
                await target.send(embed=embed)
                return
        await target.send(embed=embed)
        await interaction.followup.send(f"Announcement sent to {target.mention}! ✅", ephemeral=True)
    except Exception as e:
        print(f"ANNOUNCE ERROR: {e}")
        await interaction.followup.send(f"Couldn't announce there: {e}", ephemeral=True)

    @bot.tree.command(name="warn", description="Warn a member. Staff only.")
    @app_commands.describe(user="Who to warn?", reason="Why are they being warned?")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warn(interaction: discord.Interaction, user: discord.Member, reason: str) -> None:
        await interaction.response.send_message(embed=brand_embed("⚠️ WARNING ⚠️", f"{user.mention} has been warned.\n\n**Reason:** {reason}\n**By:** {interaction.user.mention}"), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
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

    # ===== SECURITY PACK - FIXED =====
    @bot.tree.command(name="lock", description="Lock the current channel. Staff only.")
    @app_commands.describe(channel="Which channel to lock? (leave empty for this channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def lock(interaction: discord.Interaction, channel: discord.TextChannel | None = None) -> None:
        target = channel or interaction.channel
        overwrite = target.overwrites_for(interaction.guild.default_role)
        if overwrite.send_messages is False:
            await interaction.response.send_message(embed=brand_embed("🔒 Already Locked", f"{target.mention} is already locked."), ephemeral=True)
            return
        try:
            await target.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message(embed=brand_embed("🔒 Channel Locked", f"{target.mention} is now locked.\n\nLocked by {interaction.user.mention}"), ephemeral=True)
        except Exception as e:
            print(f"LOCK ERROR: {e}")
            await interaction.response.send_message(f"Couldn't lock: {e}", ephemeral=True)

    @bot.tree.command(name="unlock", description="Unlock the current channel. Staff only.")
    @app_commands.describe(channel="Which channel to unlock? (leave empty for this channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def unlock(interaction: discord.Interaction, channel: discord.TextChannel | None = None) -> None:
        target = channel or interaction.channel
        overwrite = target.overwrites_for(interaction.guild.default_role)
        if overwrite.send_messages is not False:
            await interaction.response.send_message(embed=brand_embed("🔓 Already Unlocked", f"{target.mention} is already unlocked."), ephemeral=True)
            return
        try:
            await target.set_permissions(interaction.guild.default_role, send_messages=None)
            await interaction.response.send_message(embed=brand_embed("🔓 Channel Unlocked", f"{target.mention} is now unlocked.\n\nUnlocked by {interaction.user.mention}"), ephemeral=True)
        except Exception as e:
            print(f"UNLOCK ERROR: {e}")
            await interaction.response.send_message(f"Couldn't unlock: {e}", ephemeral=True)

    @bot.tree.command(name="lockdown", description="Lock ALL channels in the server. Admin only.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def lockdown(interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            count = 0
            for ch in interaction.guild.text_channels:
                overwrite = ch.overwrites_for(interaction.guild.default_role)
                if overwrite.send_messages is False:
                    continue
                await ch.set_permissions(interaction.guild.default_role, send_messages=False)
                count += 1
            if count == 0:
                await interaction.followup.send(embed=brand_embed("🚨 Already in Lockdown", "All channels are already locked."), ephemeral=True)
            else:
                await interaction.followup.send(embed=brand_embed("🚨 SERVER LOCKDOWN", f"Locked **{count}** channels.\n\nActivated by {interaction.user.mention}"), ephemeral=True)
        except Exception as e:
            print(f"LOCKDOWN ERROR: {e}")
            await interaction.followup.send(f"Lockdown failed: {e}", ephemeral=True)

    @bot.tree.command(name="unlockdown", description="Unlock ALL channels in the server. Admin only.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def unlockdown(interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            count = 0
            for ch in interaction.guild.text_channels:
                overwrite = ch.overwrites_for(interaction.guild.default_role)
                if overwrite.send_messages is not False:
                    continue
                await ch.set_permissions(interaction.guild.default_role, send_messages=None)
                count += 1
            if count == 0:
                await interaction.followup.send(embed=brand_embed("✅ Already Unlocked", "All channels are already unlocked."), ephemeral=True)
            else:
                await interaction.followup.send(embed=brand_embed("✅ SERVER UNLOCKED", f"Unlocked **{count}** channels.\n\nUnlocked by {interaction.user.mention}"), ephemeral=True)
        except Exception as e:
            print(f"UNLOCKDOWN ERROR: {e}")
            await interaction.followup.send(f"Unlockdown failed: {e}", ephemeral=True)

    @bot.tree.command(name="antiraid", description="Toggle anti-raid protection. Admin only.")
    @app_commands.describe(mode="Turn anti-raid on or off?")
    @app_commands.choices(mode=[app_commands.Choice(name="ON", value="on"), app_commands.Choice(name="OFF", value="off")])
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def antiraid(interaction: discord.Interaction, mode: app_commands.Choice[str]) -> None:
        await interaction.response.send_message(embed=brand_embed("🛡️ Anti-Raid", f"Anti-Raid is now **{mode.value.upper()}**.\n\nSet by {interaction.user.mention}"), ephemeral=True)

    # ===== GIVEAWAY - FIXED =====
    @bot.tree.command(name="giveaway", description="Start a giveaway. Staff only.")
    @app_commands.describe(duration="Minutes (e.g. 5)", prize="What are you giving away?")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def giveaway(interaction: discord.Interaction, duration: int, prize: str):
        embed = brand_embed("🎁 GIVEAWAY 🎁", f"**Prize:** {prize}\n\n**Ends in:** {duration} min\n**Hosted by:** {interaction.user.mention}\n\nClick 🎉 to enter!")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🎉")
        _giveaways[msg.id] = (prize, interaction.user.mention)
        channel_id = interaction.channel_id
        host_mention = interaction.user.mention
        await asyncio.sleep(duration * 60)
        try:
            channel = bot.get_channel(channel_id)
            if channel is None:
                channel = await bot.fetch_channel(channel_id)
            fresh = await channel.fetch_message(msg.id)
            users = []
            for r in fresh.reactions:
                if str(r.emoji) == "🎉":
                    async for u in r.users(limit=None):
                        if not u.bot:
                            users.append(u)
            print(f"GIVEAWAY DEBUG: Found {len(users)} users for {prize}")
            if not users:
                await channel.send(embed=brand_embed("🎁 Giveaway Ended", f"No one entered for **{prize}** 😢"))
            else:
                winner = random.choice(users)
                await channel.send(embed=brand_embed("🎉 WINNER! 🎉", f"{winner.mention} won **{prize}**!\nHosted by {host_mention}"), allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
            _giveaways.pop(msg.id, None)
        except Exception as e:
            print(f"GIVEAWAY ERROR: {e}")
            try:
                channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
                await channel.send(f"Giveaway for **{prize}** failed to pick winner: `{e}`")
            except Exception as e2:
                print(f"GIVEAWAY SEND ERROR: {e2}")
    # ===== ECONOMY =====
    @bot.tree.command(name="balance", description="Check your coins.")
    async def balance(interaction: discord.Interaction, user: discord.User | None = None):
        u = user or interaction.user
        await interaction.response.send_message(embed=brand_embed("💰 Balance", f"{u.mention} has **{_get_bal(u.id)}** coins 🪙"), ephemeral=True)

    @bot.tree.command(name="daily", description="Claim your daily coins.")
    async def daily(interaction: discord.Interaction):
        now = time.time()
        last = _daily_claimed.get(interaction.user.id, 0)
        if now - last < 86400:
            hrs = int((86400 - (now - last)) / 3600)
            await interaction.response.send_message(embed=brand_embed("⏳ Daily", f"Already claimed! Come back in **{hrs}h**"), ephemeral=True)
            return
        _daily_claimed[interaction.user.id] = now
        _balances[interaction.user.id] = _get_bal(interaction.user.id) + 500
        await interaction.response.send_message(embed=brand_embed("💰 Daily Claimed!", f"+500 coins! 🪙\nNew balance: **{_get_bal(interaction.user.id)}**"))

    @bot.tree.command(name="work", description="Work for coins.")
    async def work(interaction: discord.Interaction):
        jobs = ["You coded for NEXUS 💻", "You guarded the server 🛡️", "You sold memes 😂", "You streamed on Twitch 🎮"]
        earn = random.randint(50, 250)
        _balances[interaction.user.id] = _get_bal(interaction.user.id) + earn
        await interaction.response.send_message(embed=brand_embed("💼 Work", f"{random.choice(jobs)}\n+**{earn}** coins! Balance: **{_get_bal(interaction.user.id)}**"))

    @bot.tree.command(name="pay", description="Pay someone coins.")
    @app_commands.describe(user="Who to pay?", amount="How much?")
    async def pay(interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Amount must be > 0", ephemeral=True); return
        if _get_bal(interaction.user.id) < amount:
            await interaction.response.send_message(f"You only have {_get_bal(interaction.user.id)} coins!", ephemeral=True); return
        _balances[interaction.user.id] -= amount
        _balances[user.id] = _get_bal(user.id) + amount
        await interaction.response.send_message(embed=brand_embed("💸 Payment", f"{interaction.user.mention} paid {user.mention} **{amount}** coins 🪙"))
        
    # ===== TICKET PANEL V2 =====
    @bot.tree.command(name="ticket-panel", description="Post ticket panel. Admin only.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(interaction: discord.Interaction):
        await interaction.response.send_message(embed=brand_embed("🎫 NEXUS Support", "Need help? Click below to open a ticket!\n\nOur staff will assist you ASAP."), view=TicketView())

    @bot.tree.command(name="help", description="See all NEXUS commands.")
    async def help_cmd(interaction: discord.Interaction) -> None:
        text = (
            "**👋 Welcome / Fun**\n"
            "`/hello` `/greet` `/goodmorning` `/goodnight` `/shoutout` `/roast` `/8ball`\n\n"
            "**📊 Community**\n"
            "`/poll` `/rank` `/leaderboard`\n\n"
            "**📢 Staff**\n"
            "`/send` `/dm` `/announce` `/warn` `/ban` `/kick` `/mute` `/unmute` `/unban` `/clear`\n\n"
            "**🛡️ Security**\n"
            "`/antinuke` `/lock` `/unlock` `/lockdown` `/unlockdown` `/antiraid`\n\n"
            "**🎁 Giveaway**\n"
            "`/giveaway`\n\n"
            "**💰 Economy**\n"
            "`/balance` `/daily` `/work` `/pay`\n\n"
            "**🎫 Tickets**\n"
            "`/ticket-panel`\n\n"
            "**⚙️ Setup / System**\n"
            "`/ping` `/verify` `/ticket-setup` `/reaction-role-setup` `/welcome set` `/list-roles` `/automod`\n\n"
            "**Tip:** Use `/poll` to vote, `/roast` to have fun, `/announce` for big news!"
        )
        await interaction.response.send_message(embed=brand_embed("🤖 NEXUS V1 - All Commands", text), ephemeral=True)

async def handle_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        message = "You do not have permission to use that command."
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "This command can only be used inside a server."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = "That command is being used too quickly. Try again shortly."
    else:
        original = getattr(error, "original", error)
        command_name = interaction.command.qualified_name if interaction.command is not None else "unknown"
        logger.error("Slash command %s failed with %s", command_name, type(original).__name__)
        if isinstance(original, discord.Forbidden):
            message = "I could not complete that action. Check my permissions and role position."
        else:
            message = "That command failed. Check the bot's permissions and try again."
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except discord.HTTPException:
        logger.debug("Could not send slash-command error response.")