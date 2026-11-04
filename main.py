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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")


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
        self.add_view(VerifyView(self.store))
        register_ticket_views(self, self.store)
        commands_synced = await self.tree.sync()
        logger.info("Synced %d slash command(s).", len(commands_synced))

    async def on_ready(self) -> None:
        if self.user is not None:
            logger.info("NEXUS V1 online as %s (ID: %s)", self.user, self.user.id)

    async def on_member_join(self, member: discord.Member) -> None:
        await handle_member_join(self.store, member)

    async def on_message(self, message: discord.Message) -> None:
        if await handle_automod(self.store, message):
            return
        await handle_level_message(self.store, message)

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
