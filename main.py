import logging
import os

import discord
from discord import app_commands
from discord.ext import commands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot")


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.default(),
        )

    async def setup_hook(self) -> None:
        commands_synced = await self.tree.sync()
        logger.info("Synced %d slash command(s).", len(commands_synced))

    async def on_ready(self) -> None:
        if self.user is not None:
            logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)


bot = DiscordBot()


@bot.tree.command(name="ping", description="Check whether the bot is online.")
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency_ms} ms")


@bot.tree.command(name="hello", description="Say hello to the bot.")
async def hello(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}!"
    )


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
