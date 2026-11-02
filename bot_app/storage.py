from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import aiosqlite


DEFAULT_SETTINGS: dict[str, Any] = {
    "welcome_channel_id": None,
    "verified_role_id": None,
    "ticket_category_id": None,
    "support_role_id": None,
    "channel_lock_overwrites": {},
    "automod_enabled": False,
    "automod_block_invites": True,
    "automod_max_mentions": 5,
    "automod_spam_limit": 6,
}


class BotStore:
    """Small SQLite store for settings and member progress across restarts."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured_path = path or os.getenv(
            "NEXUS_DB_PATH", "bot_data/nexus_v1.sqlite3"
        )
        self.path = Path(configured_path)
        self._db: aiosqlite.Connection | None = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("The NEXUS database has not been initialized.")
        return self._db

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.path))
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode = WAL")
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                config TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                opened_at INTEGER NOT NULL DEFAULT (unixepoch()),
                closed_at INTEGER
            );

            CREATE UNIQUE INDEX IF NOT EXISTS one_open_ticket_per_member
                ON tickets(guild_id, user_id)
                WHERE closed_at IS NULL;

            CREATE TABLE IF NOT EXISTS member_xp (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total_xp INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS reaction_roles (
                message_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (message_id, emoji)
            );

            CREATE TABLE IF NOT EXISTS member_warnings (
                warning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at INTEGER NOT NULL DEFAULT (unixepoch()),
                cleared_at INTEGER,
                cleared_by INTEGER
            );

            CREATE INDEX IF NOT EXISTS member_warnings_by_user
                ON member_warnings(guild_id, user_id, warning_id);
            """
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def get_settings(self, guild_id: int) -> dict[str, Any]:
        async with self.db.execute(
            "SELECT config FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return DEFAULT_SETTINGS.copy()

        saved = json.loads(row["config"])
        return {**DEFAULT_SETTINGS, **saved}

    async def set_settings(self, guild_id: int, **updates: Any) -> dict[str, Any]:
        settings = await self.get_settings(guild_id)
        settings.update(updates)
        await self.db.execute(
            """
            INSERT INTO guild_settings (guild_id, config)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET config = excluded.config
            """,
            (guild_id, json.dumps(settings)),
        )
        await self.db.commit()
        return settings

    async def create_ticket(
        self, guild_id: int, channel_id: int, user_id: int
    ) -> int:
        cursor = await self.db.execute(
            """
            INSERT INTO tickets (guild_id, channel_id, user_id)
            VALUES (?, ?, ?)
            """,
            (guild_id, channel_id, user_id),
        )
        await self.db.commit()
        return int(cursor.lastrowid)

    async def get_open_ticket(
        self, guild_id: int, user_id: int
    ) -> aiosqlite.Row | None:
        async with self.db.execute(
            """
            SELECT ticket_id, guild_id, channel_id, user_id, opened_at, closed_at
            FROM tickets
            WHERE guild_id = ? AND user_id = ? AND closed_at IS NULL
            """,
            (guild_id, user_id),
        ) as cursor:
            return await cursor.fetchone()

    async def get_ticket_by_channel(self, channel_id: int) -> aiosqlite.Row | None:
        async with self.db.execute(
            """
            SELECT ticket_id, guild_id, channel_id, user_id, opened_at, closed_at
            FROM tickets
            WHERE channel_id = ?
            """,
            (channel_id,),
        ) as cursor:
            return await cursor.fetchone()

    async def close_ticket(self, channel_id: int) -> None:
        await self.db.execute(
            """
            UPDATE tickets
            SET closed_at = unixepoch()
            WHERE channel_id = ? AND closed_at IS NULL
            """,
            (channel_id,),
        )
        await self.db.commit()

    async def add_xp(self, guild_id: int, user_id: int, amount: int) -> int:
        await self.db.execute(
            """
            INSERT INTO member_xp (guild_id, user_id, total_xp)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET total_xp = member_xp.total_xp + excluded.total_xp
            """,
            (guild_id, user_id, amount),
        )
        await self.db.commit()
        return await self.get_xp(guild_id, user_id)

    async def get_xp(self, guild_id: int, user_id: int) -> int:
        async with self.db.execute(
            """
            SELECT total_xp FROM member_xp
            WHERE guild_id = ? AND user_id = ?
            """,
            (guild_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["total_xp"]) if row else 0

    async def get_leaderboard(
        self, guild_id: int, limit: int = 10
    ) -> list[aiosqlite.Row]:
        async with self.db.execute(
            """
            SELECT user_id, total_xp
            FROM member_xp
            WHERE guild_id = ?
            ORDER BY total_xp DESC, user_id ASC
            LIMIT ?
            """,
            (guild_id, limit),
        ) as cursor:
            return list(await cursor.fetchall())

    async def set_reaction_role(
        self, message_id: int, emoji: str, guild_id: int, role_id: int
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO reaction_roles (message_id, emoji, guild_id, role_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(message_id, emoji)
            DO UPDATE SET guild_id = excluded.guild_id, role_id = excluded.role_id
            """,
            (message_id, emoji, guild_id, role_id),
        )
        await self.db.commit()

    async def get_reaction_role(
        self, message_id: int, emoji: str
    ) -> aiosqlite.Row | None:
        async with self.db.execute(
            """
            SELECT guild_id, role_id
            FROM reaction_roles
            WHERE message_id = ? AND emoji = ?
            """,
            (message_id, emoji),
        ) as cursor:
            return await cursor.fetchone()

    async def add_warning(
        self,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
    ) -> int:
        cursor = await self.db.execute(
            """
            INSERT INTO member_warnings (guild_id, user_id, moderator_id, reason)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, user_id, moderator_id, reason),
        )
        await self.db.commit()
        return int(cursor.lastrowid)

    async def get_warnings(
        self,
        guild_id: int,
        user_id: int,
        *,
        limit: int = 10,
    ) -> list[aiosqlite.Row]:
        async with self.db.execute(
            """
            SELECT warning_id, moderator_id, reason, created_at
            FROM member_warnings
            WHERE guild_id = ? AND user_id = ? AND cleared_at IS NULL
            ORDER BY warning_id DESC
            LIMIT ?
            """,
            (guild_id, user_id, max(1, min(int(limit), 50))),
        ) as cursor:
            return list(await cursor.fetchall())

    async def count_warnings(self, guild_id: int, user_id: int) -> int:
        async with self.db.execute(
            """
            SELECT COUNT(*) AS warning_count
            FROM member_warnings
            WHERE guild_id = ? AND user_id = ? AND cleared_at IS NULL
            """,
            (guild_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
        return int(row["warning_count"]) if row else 0

    async def clear_warning(
        self,
        guild_id: int,
        user_id: int,
        warning_id: int,
        moderator_id: int,
    ) -> bool:
        cursor = await self.db.execute(
            """
            UPDATE member_warnings
            SET cleared_at = unixepoch(), cleared_by = ?
            WHERE guild_id = ?
              AND user_id = ?
              AND warning_id = ?
              AND cleared_at IS NULL
            """,
            (moderator_id, guild_id, user_id, warning_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0
