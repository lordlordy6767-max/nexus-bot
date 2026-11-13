import os
import urllib.parse
import aiohttp
import io
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"NEXUS is online")
    def log_message(self, *args):
        pass

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()
import logging
import os

import discord
from discord import app_commands

from bot_app.automod import handle_automod
from bot_app.commands import handle_app_command_error, register_commands
from bot_app.levels import handle_level_message
from bot_app.onboarding import VerifyView, handle_member_join
from bot_app.reaction_roles import handle_reaction
from bot_app.storage import BotStore
from bot_app.tickets import register_ticket_views
from bot_app.tag_replies import handle_tag_reply
from bot_app.userinfo import register_info_commands
from bot_app.games import register_games_commands
from bot_app.moderation import register_farewell
from bot_app.v3 import register_v3
from bot_app.comeback import handle_comeback
from bot_app.ai_brain import ask_nexus, translate_smart, is_owner
from bot_app.Nexus_premium import check_paywall, unlock, lock, create_channels, create_categories, create_roles, create_voice, move_channels, set_role_color, rename_channel, rename_category
# --- NEW: PREMIUM ALL ---
from bot_app import premium_all
from bot_app.premium_all import convert_font, list_fonts, build_list_embed, apply_font_if_any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")

GUILD_ID = 0

class NexusBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.store = BotStore()
        self.tree.on_error = handle_app_command_error

    async def setup_hook(self) -> None:
        await self.store.initialize()
        register_commands(self, self.store)
        register_info_commands(self, self.store)
        register_games_commands(self, self.store)
        register_farewell(self)
        register_v3(self, self.store)
        self.add_view(VerifyView(self.store))
        register_ticket_views(self, self.store)
        commands_synced = await self.tree.sync()
        logger.info("Synced %d slash command(s).", len(commands_synced))
        if GUILD_ID != 0:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            guild_synced = await self.tree.sync(guild=guild)
            logger.info("Synced %d guild command(s).", len(guild_synced))

    async def on_ready(self) -> None:
        if self.user is not None:
            logger.info("NEXUS V1 online as %s (ID: %s)", self.user, self.user.id)

    async def on_member_join(self, member: discord.Member) -> None:
        await handle_member_join(self.store, member)
        # AutoRole - premium_all
        try: await premium_all.give_autorole(member)
        except: pass

    async def on_message(self, message):
        if message.author.bot:
            return

        if await handle_comeback(self, message):
            return
        # --- STORY MODE ---
        if not message.author.bot and message.guild and self.user in message.mentions:
            text = message.content.lower()
            if "tell" in text and "story" in text or "story time" in text:
                from bot_app.story import get_story
                kind = None
                if "spooky" in text or "scary" in text or "horror" in text or "creepy" in text:
                    kind = "spooky"
                elif "sweet" in text or "cute" in text or "love" in text or "wholesome" in text:
                    kind = "sweet"
                elif "funny" in text or "joke" in text or "laugh" in text:
                    kind = "funny"
                elif "motivational" in text or "inspire" in text or "motivate" in text:
                    kind = "motivational"
                kind, story = get_story(kind)
                emoji = {"spooky": "👻", "sweet": "💛", "funny": "😂", "motivational": "🔥"}.get(kind, "📖")
                await message.reply(f"{emoji} **{kind.capitalize()} Story Time**\n\n{story}\n\n*Want another? Say `@NEXUS tell me a spooky story` or `sweet / funny / motivational`*")
                return

        if await handle_tag_reply(self, message):
            return

        # --- AFK: if someone mentions AFK user, show it / if AFK user talks, remove ---
        if message.guild and message.mentions:
            for u in message.mentions:
                r = premium_all.get_afk(message.guild.id, u.id)
                if r:
                    await message.reply(f"💤 {u.display_name} is AFK: {r}")
                    break
        if message.guild and premium_all.get_afk(message.guild.id, message.author.id):
            premium_all.remove_afk(message.guild.id, message.author.id)
            await message.reply(f"👋 Welcome back {message.author.display_name}, AFK removed.")

        # --- NEXUS PREMIUM ---
        if message.content.startswith("!unlock"):
            if not is_owner(message.author.id):
                await message.reply("❌ Only Starr can unlock.")
                return
            if message.mentions:
                target = message.mentions[0]
                await message.reply(unlock(target.id, message.author.id))
            else:
                await message.reply("Use: `!unlock @user`")
            return

        if message.content.startswith("!lock"):
            if not is_owner(message.author.id):
                await message.reply("❌ Only Starr can lock.")
                return
            if message.mentions:
                target = message.mentions[0]
                await message.reply(lock(target.id, message.author.id))
            else:
                await message.reply("Use: `!lock @user`")
            return

        # --- !list - FREE for everyone to see, premium to use ---
        if message.content.strip() == "!list":
            await message.reply(embed=build_list_embed())
            return

        # --- FONTS - PREMIUM ---
        if message.content.startswith("!fonts"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(list_fonts()); return

        if message.content.startswith("!font "):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            parts = message.content.split(" ", 2)
            if len(parts) < 3:
                await message.reply("Use: `!font bold Hello`"); return
            await message.reply(convert_font(parts[2], parts[1])); return

        if message.content.startswith("!big "):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(convert_font(message.content[5:].strip(), "big")); return

        if message.content.startswith("!small "):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(convert_font(message.content[7:].strip(), "small")); return

        if message.content.startswith("!create"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked)
                return
            parts = message.content.split(" ", 2)
            if len(parts) < 3:
                await message.reply("Use: `!create channels memes, clips` / `!create roles vip red` / `!create categories Gaming` / `!create voice Chill` / `!create categories big Gaming`")
                return
            kind = parts[1].lower()
            names = parts[2]
            # FONTS IN CREATE: !create categories big Gaming / !create roles bold VIP red
            # If first word is a font, convert the rest before creating
            words = names.split()
            if words and words[0].lower() in premium_all.FONTS:
                font = words[0].lower()
                rest = " ".join(words[1:])
                # convert each comma part separately, keep color word if roles
                if kind in ["roles", "role"]:
                    new_parts = []
                    for p in rest.split(","):
                        pw = p.strip().split()
                        if len(pw) >= 2:
                            new_parts.append(convert_font(pw[0], font) + " " + " ".join(pw[1:]))
                        elif pw:
                            new_parts.append(convert_font(pw[0], font))
                    names = ", ".join(new_parts)
                else:
                    names = convert_font(rest, font)
            if kind in ["channels", "channel"]:
                res = await create_channels(message.guild, names)
            elif kind in ["roles", "role"]:
                res = await create_roles(message.guild, names)
            elif kind in ["categories", "category"]:
                res = await create_categories(message.guild, names)
            elif kind in ["voice"]:
                res = await create_voice(message.guild, names)
            else:
                res = "Use: channels / roles / categories / voice"
            await message.reply(res)
            return

        if message.content.startswith("!move"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked)
                return
            try:
                content = message.content.replace("!move ", "", 1).strip()
                left, cat = content.rsplit(" to ", 1)
                res = await move_channels(message.guild, left.strip(), cat.strip())
                await message.reply(res)
            except:
                await message.reply("Use: `!move memes, clips to Gaming` / `!move #memes #clips to Gaming`")
            return

        if message.content.startswith("!rename"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked)
                return
            try:
                content = message.content.replace("!rename ", "", 1).strip()
                left, new_name = content.rsplit(" to ", 1)
                res = await rename_channel(message.guild, left.strip(), new_name.strip())
                await message.reply(res)
            except:
                await message.reply("Use: `!rename #general to chat` / `!rename Gaming to New Gaming`")
            return

        if message.content.startswith("!color"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked)
                return
            try:
                parts = message.content.replace("!color ", "", 1).strip().split()
                if len(parts) < 2:
                    await message.reply("Use: `!color vip red` / `!color admin FF0000`")
                    return
                res = await set_role_color(message.guild, parts[0], parts[1])
                await message.reply(res)
            except:
                await message.reply("Use: `!color vip red`")
            return

        # --- NEW PREMIUM ALL COMMANDS ---
        if message.content.startswith("!autorole"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            if message.role_mentions:
                await message.reply(premium_all.set_autorole(message.guild.id, message.role_mentions[0].id))
            else:
                await message.reply("Use: `!autorole @Member`"); return
            return

        if message.content.startswith("!removeautorole"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(premium_all.remove_autorole(message.guild.id)); return

        if message.content.startswith("!levelroles"):
            await message.reply(premium_all.list_level_roles(message.guild.id)); return

        if message.content.startswith("!levelrole"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            try:
                parts = message.content.split()
                lvl = parts[1]
                role = message.role_mentions[0]
                await message.reply(premium_all.set_level_role(message.guild.id, lvl, role.id))
            except:
                await message.reply("Use: `!levelrole 10 @VIP`")
            return

        if message.content.startswith("!afk"):
            reason = message.content.replace("!afk", "", 1).strip() or "AFK"
            premium_all.set_afk(message.guild.id, message.author.id, reason)
            await message.reply(f"💤 AFK set: {reason}"); return

        if message.content.startswith("!addcmd"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            try:
                parts = message.content.split(" ", 2)
                await message.reply(premium_all.add_custom_cmd(message.guild.id, parts[1], parts[2]))
            except:
                await message.reply("Use: `!addcmd hello Hello!`")
            return

        if message.content.startswith("!delcmd"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            try:
                name = message.content.split()[1]
                await message.reply(premium_all.del_custom_cmd(message.guild.id, name))
            except:
                await message.reply("Use: `!delcmd hello`")
            return

        if message.content.strip() == "!cmds":
            await message.reply(premium_all.list_custom_cmds(message.guild.id)); return

        if message.content.startswith("!starboard"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            if message.channel_mentions:
                await message.reply(premium_all.set_starboard(message.guild.id, message.channel_mentions[0].id))
            else:
                await message.reply("Use: `!starboard #starboard`")
            return

        if message.content.strip() == "!backup":
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(await premium_all.make_backup(message.guild)); return

        if message.content.strip() == "!restore":
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            await message.reply(await premium_all.restore_backup(message.guild)); return

        if message.content.startswith("!massdelete"):
            try:
                parts = message.content.split()
                if len(parts) >= 3 and parts[1] == "channels":
                    if len(parts) == 4 and parts[2].isdigit():
                        count = int(parts[2]); prefix = parts[3]
                        deleted = 0
                        for n in range(1, count+1):
                            for ch in list(message.guild.channels):
                                if ch.name == f"{prefix}-{n}":
                                    await ch.delete(); deleted += 1
                        await message.channel.send(f"Deleted {deleted} channels starting with {prefix}")
                        return
                    prefix = parts[2]
                    deleted = 0
                    for ch in list(message.guild.channels):
                        if ch.name.startswith(prefix):
                            await ch.delete()
                            deleted += 1
                    await message.channel.send(f"Deleted {deleted} channels starting with {prefix}")
                    return
                await message.channel.send("Which channels should I delete? Reply with names separated by comma.\nExample: `gaming, music, chat`\nOr reply `all text` / `all voice` / `cancel`")
                def check(m):
                    return m.author == message.author and m.channel == message.channel
                try:
                    reply = await client.wait_for("message", check=check, timeout=60.0)
                except:
                    await message.channel.send("Timed out - no channels deleted.")
                    return
                text = reply.content.strip().lower()
                if text == "cancel":
                    await message.channel.send("Cancelled - nothing deleted.")
                    return
                deleted = 0
                notfound = []
                if text == "all text":
                    for ch in list(message.guild.text_channels):
                        if ch != message.channel:
                            await ch.delete()
                            deleted += 1
                elif text == "all voice":
                    for ch in list(message.guild.voice_channels):
                        await ch.delete()
                        deleted += 1
                else:
                    names = [n.strip().lower() for n in reply.content.split(",")]
                    for name in names:
                        found = False
                        for ch in list(message.guild.channels):
                            if ch.name.lower() == name:
                                await ch.delete()
                                deleted += 1
                                found = True
                        if not found:
                            notfound.append(name)
                msg = f"Deleted {deleted} channels."
                if notfound:
                    msg += " Not found: " + ", ".join(notfound)
                await message.channel.send(msg)
            except Exception as e:
                await message.channel.send(f"Delete failed: {e}")
            return

        if message.content.startswith("!masscreate"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            try:
                parts = message.content.split()
                # !masscreate channels 5 gaming
                kind = parts[1]; count = parts[2]; base = parts[3]
                await message.reply(await premium_all.mass_create(message.guild, kind, count, base))
            except:
                await message.reply("Use: `!masscreate channels 5 gaming`")
                return

        if message.content.startswith("!aiimage"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            prompt = message.content.replace("!aiimage", "", 1).strip()
            style_suffix = ""
            if prompt.lower().startswith("anime "):
                prompt = prompt[6:].strip()
                style_suffix = ", anime style, vibrant, detailed anime art"
            prompt = prompt + style_suffix
            if not prompt:
                await message.reply("Use: `!aiimage a dragon`"); return
        await message.reply(f"🎨 Making: **{prompt}**...")
        import random
        encoded = urllib.parse.quote(prompt)
        data = None
        for attempt in range(3):
            seed = random.randint(1, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.read()
                        # Check if it's really an image (PNG starts with this)
                        if len(data) > 10000:
                            break
                        print(f"Retry {attempt} got {len(data)} bytes")
            except Exception as e:
                print(f"Retry {attempt} error: {e}")
                continue
        if not data or len(data) < 10000:
            await message.reply("Pollinations is busy right now, try again in 10 seconds!")
        else:
            file = discord.File(io.BytesIO(data), filename="nexus-ai.png")
            await message.reply(file=file)
        return
    

        if message.content.startswith("!giveawayrole"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked); return
            # !giveawayrole 1h Nitro @VIP -> shows who can join
            clean, role_id = premium_all.parse_giveaway_role(message.content.replace("!giveawayrole", "", 1).strip())
            if role_id:
                await message.reply(f"🎁 Giveaway: **{clean}** - Only <@&{role_id}> can join! Use your normal `!giveaway` + this check.")
            else:
                await message.reply(f"🎁 Giveaway: **{clean}** - Everyone can join.")
            return

        # Custom commands run - FREE if already created, but creation is premium
        if message.content.startswith("!") and message.guild:
            cmd_name = message.content[1:].split()[0].lower()
            custom = premium_all.get_custom_cmd(message.guild.id, cmd_name)
            if custom:
                await message.reply(custom); return

        if message.content.startswith("!translate"):
            raw = message.content.replace("!translate", "", 1).strip()
            if not raw:
                await message.reply("Use: `!translate come stai` / `!translate hindi hello` / `!translate hello in hindi`")
                return
            await message.reply(translate_smart(raw))
            return
        # --- END PREMIUM ---
        # --- NEXUS AI BRAIN ---
        if self.user in message.mentions and message.guild and not message.author.bot:
            content = message.content
            content = content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
            if content:
                async with message.channel.typing():
                    reply = ask_nexus(content, message.author.name, channel_id=str(message.channel.id), user_id=message.author.id)
                await message.reply(reply)
                return
        # --- END AI BRAIN ---

        if await handle_automod(self.store, message):
            return
        await handle_level_message(message)
        # Level roles check - if user leveled, give role (levels.py handles XP, this is best-effort)
        # Note: if your levels system has level in message, this will be handled via premium_all.check_level_roles in future

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await handle_reaction(self, self.store, payload, added=True)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await handle_reaction(self, self.store, payload, added=False)

    async def close(self) -> None:
        await self.store.close()
        await super().close()
    async def on_guild_join(self, guild):
        try:
            owner = await self.fetch_user(1545810202232885258)
            await owner.send(
                f"👑 **NEXUS joined a new server!**\n"
                f"**Server:** {guild.name}\n"
                f"**Members:** {guild.member_count}\n"
                f"**Server ID:** {guild.id}\n"
                f"**Total servers now:** {len(self.guilds)}"
            )
        except Exception as e:
            print(f"Join log failed: {e}")

def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error(
            "DISCORD_BOT_TOKEN is missing. Add your bot token in Replit Secrets."
        )
        raise SystemExit(1)

    bot.run(token, log_handler=None)

if __name__ == "__main__":
    main()
