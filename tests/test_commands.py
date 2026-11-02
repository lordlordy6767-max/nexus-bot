from __future__ import annotations

import unittest

import discord
from discord import app_commands

from bot_app.commands import HELP_CATEGORIES, build_help_embed, register_commands
from bot_app.levels import level_for_xp, next_level_xp
from bot_app.storage import BotStore


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_feature_commands_register(self) -> None:
        client = discord.Client(intents=discord.Intents.none())
        client.tree = app_commands.CommandTree(client)
        register_commands(client, BotStore(":memory:"))

        commands = {command.name: command for command in client.tree.get_commands()}
        expected = {
            "verify",
            "welcome",
            "automod",
            "ban",
            "kick",
            "clear",
            "mute",
            "warn",
            "warnings",
            "unwarn",
            "unban",
            "unmute",
            "userinfo",
            "serverinfo",
            "avatar",
            "lock",
            "unlock",
            "slowmode",
            "ticket-setup",
            "reaction-role-setup",
            "rank",
            "leaderboard",
            "help",
            "ping",
            "hello",
        }
        self.assertEqual(set(commands), expected)
        self.assertEqual(
            {command.name for command in commands["welcome"].commands},
            {"set", "disable"},
        )
        self.assertEqual(
            {command.name for command in commands["automod"].commands},
            {"configure", "status"},
        )
        await client.close()

    def test_help_covers_all_requested_categories_and_commands(self) -> None:
        embed = build_help_embed()
        self.assertEqual(
            [field.name for field in embed.fields],
            [
                "MODERATION",
                "AUTOMOD & LOGS",
                "WELCOME & VERIFY",
                "LEVELS",
                "TICKETS & ROLES",
                "UTILITY",
            ],
        )
        content = "\n".join(field.value for field in embed.fields)
        for command in (
            "/warn",
            "/warnings",
            "/unwarn",
            "/unban",
            "/unmute",
            "/userinfo",
            "/serverinfo",
            "/avatar",
            "/lock",
            "/unlock",
            "/slowmode",
            "/ticket-setup",
            "/reaction-role-setup",
            "/automod configure",
            "/welcome set",
        ):
            self.assertIn(command, content)
        self.assertEqual(len(HELP_CATEGORIES), 6)

    def test_level_boundaries(self) -> None:
        self.assertEqual(level_for_xp(0), 0)
        self.assertEqual(level_for_xp(99), 0)
        self.assertEqual(level_for_xp(100), 1)
        self.assertEqual(level_for_xp(399), 1)
        self.assertEqual(level_for_xp(400), 2)
        self.assertEqual(next_level_xp(2), 900)


if __name__ == "__main__":
    unittest.main()
