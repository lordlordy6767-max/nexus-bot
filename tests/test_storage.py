from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from sqlite3 import IntegrityError

from bot_app.storage import BotStore


class BotStoreTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "nexus.sqlite3"
        self.store = BotStore(self.database_path)
        await self.store.initialize()

    async def asyncTearDown(self) -> None:
        await self.store.close()
        self.temp_dir.cleanup()

    async def test_guild_settings_survive_reopen(self) -> None:
        await self.store.set_settings(
            1001,
            welcome_channel_id=2002,
            moderation_log_channel_id=2010,
            automod_enabled=True,
        )
        await self.store.close()

        reopened = BotStore(self.database_path)
        await reopened.initialize()
        try:
            settings = await reopened.get_settings(1001)
            self.assertEqual(settings["welcome_channel_id"], 2002)
            self.assertEqual(settings["moderation_log_channel_id"], 2010)
            self.assertTrue(settings["automod_enabled"])
            self.assertEqual(settings["automod_max_mentions"], 5)
        finally:
            await reopened.close()

    async def test_ticket_lifecycle(self) -> None:
        await self.store.create_ticket(1001, 3003, 4004)

        ticket = await self.store.get_open_ticket(1001, 4004)
        self.assertIsNotNone(ticket)
        assert ticket is not None
        self.assertEqual(ticket["channel_id"], 3003)

        await self.store.close_ticket(3003)
        self.assertIsNone(await self.store.get_open_ticket(1001, 4004))
        closed_ticket = await self.store.get_ticket_by_channel(3003)
        self.assertIsNotNone(closed_ticket)
        assert closed_ticket is not None
        self.assertIsNotNone(closed_ticket["closed_at"])

    async def test_member_cannot_have_two_open_tickets(self) -> None:
        await self.store.create_ticket(1001, 3003, 4004)
        with self.assertRaises(IntegrityError):
            await self.store.create_ticket(1001, 3004, 4004)

    async def test_xp_and_leaderboard(self) -> None:
        self.assertEqual(await self.store.add_xp(1001, 4004, 20), 20)
        self.assertEqual(await self.store.add_xp(1001, 4004, 25), 45)
        await self.store.add_xp(1001, 5005, 30)

        leaderboard = await self.store.get_leaderboard(1001)
        self.assertEqual(
            [(row["user_id"], row["total_xp"]) for row in leaderboard],
            [(4004, 45), (5005, 30)],
        )

    async def test_reaction_role_mapping(self) -> None:
        await self.store.set_reaction_role(6006, "✅", 1001, 7007)

        mapping = await self.store.get_reaction_role(6006, "✅")
        self.assertIsNotNone(mapping)
        assert mapping is not None
        self.assertEqual(mapping["guild_id"], 1001)
        self.assertEqual(mapping["role_id"], 7007)


if __name__ == "__main__":
    unittest.main()
