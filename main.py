import os
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
from bot_app.Nexus_premium import check_paywall, unlock, create_channels, create_categories, create_roles, create_voice, move_channels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")

# --- PUT YOUR SERVER ID HERE ---
GUILD_ID = 0  # <-- PASTE YOUR SERVER ID HERE, e.g. 123456789012345678

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
        # Global sync (slow, up to 1 hour)
        commands_synced = await self.tree.sync()
        logger.info("Synced %d slash command(s).", len(commands_synced))
        # Guild sync (instant) - THIS is the fix for /antinuke not showing
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

        if message.content.startswith("!create"):
            blocked = check_paywall(message.author.id)
            if blocked:
                await message.reply(blocked)
                return
            parts = message.content.split(" ", 2)
            if len(parts) < 3:
                await message.reply("Use: `!create channels memes, clips` / `!create roles vip` / `!create categories Gaming` / `!create voice Chill`")
                return
            kind = parts[1].lower()
            names = parts[2]
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
                # Use rsplit so "to" inside channel names doesn't break it
                # !move #memes #clips to Gaming
                # !move memes, clips to 🎮-Gaming
                content = message.content.replace("!move ", "", 1).strip()
                left, cat = content.rsplit(" to ", 1)
                res = await move_channels(message.guild, left.strip(), cat.strip())
                await message.reply(res)
            except:
                await message.reply("Use: `!move memes, clips to Gaming` / `!move #memes #clips to Gaming`")
            return

        if message.content.startswith("!translate"):
            # Now uses translate_smart - handles all forms
            # !translate come stai -> English
            # !translate es hello -> Spanish
            # !translate hindi hello -> Hindi
            raw = message.content.replace("!translate", "", 1).strip()
            if not raw:
                await message.reply("Use: `!translate come stai` / `!translate es hello` / `!translate hindi hello`")
                return
            await message.reply(translate_smart(raw))
            return
        # --- END PREMIUM ---
        # --- NEXUS AI BRAIN ---
        if self.user in message.mentions and message.guild and not message.author.bot:
            content = message.content
            # remove the @NEXUS mention
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
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        await handle_reaction(self, self.store, payload, added=True)

    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        await handle_reaction(self, self.store, payload, added=False)

    async def close(self) -> None:
        await self.store.close()
        await super().close()

bot = NexusBot()

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