from __future__ import annotations

import datetime
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import discord

from bot_app.automod import handle_automod
from bot_app.commands import register_commands
from bot_app.moderation_log import send_moderation_log


class ModerationLogTests(unittest.IsolatedAsyncioTestCase):
    async def test_configure_command_accepts_private_channel(self) -> None:
        store = AsyncMock()
        client = discord.Client(intents=discord.Intents.none())
        client.tree = discord.app_commands.CommandTree(client)
        register_commands(client, store)

        default_role = object()
        bot_member = object()
        guild = SimpleNamespace(id=901, default_role=default_role, me=bot_member)
        channel = Mock(spec=discord.TextChannel)
        channel.guild = guild
        channel.id = 902
        channel.mention = "<#902>"
        bot_permissions = SimpleNamespace(
            view_channel=True,
            send_messages=True,
            embed_links=True,
        )
        public_permissions = SimpleNamespace(view_channel=False)
        channel.permissions_for = Mock(
            side_effect=lambda subject: (
                public_permissions if subject is default_role else bot_permissions
            )
        )
        interaction = SimpleNamespace(
            guild=guild,
            response=SimpleNamespace(send_message=AsyncMock()),
        )
        command_group = client.tree.get_command("moderation-log")

        assert command_group is not None
        set_command = command_group.get_command("set")
        assert set_command is not None
        await set_command.callback(interaction, channel)

        store.set_settings.assert_awaited_once_with(
            901,
            moderation_log_channel_id=902,
        )
        interaction.response.send_message.assert_awaited_once()
        self.assertTrue(
            interaction.response.send_message.await_args.kwargs["ephemeral"]
        )
        await client.close()

    async def test_public_channel_is_rejected_for_configuration(self) -> None:
        store = AsyncMock()
        client = discord.Client(intents=discord.Intents.none())
        client.tree = discord.app_commands.CommandTree(client)
        register_commands(client, store)

        default_role = object()
        bot_member = object()
        guild = SimpleNamespace(id=901, default_role=default_role, me=bot_member)
        channel = Mock(spec=discord.TextChannel)
        channel.guild = guild
        channel.permissions_for = Mock(
            return_value=SimpleNamespace(view_channel=True)
        )
        interaction = SimpleNamespace(
            guild=guild,
            response=SimpleNamespace(send_message=AsyncMock()),
        )
        command_group = client.tree.get_command("moderation-log")

        assert command_group is not None
        set_command = command_group.get_command("set")
        assert set_command is not None
        await set_command.callback(interaction, channel)

        store.set_settings.assert_not_awaited()
        warning = interaction.response.send_message.await_args.args[0]
        self.assertIn("private", warning)
        await client.close()

    async def test_log_embed_includes_actor_action_reason_and_timestamp(self) -> None:
        log_channel = Mock(spec=discord.TextChannel)
        log_channel.send = AsyncMock()
        guild = SimpleNamespace(
            id=901,
            get_channel=Mock(return_value=log_channel),
        )
        store = AsyncMock()
        store.get_settings.return_value = {"moderation_log_channel_id": 902}
        actor = Mock(spec=discord.Member)
        actor.id = 903
        actor.mention = "<@903>"
        affected = Mock(spec=discord.Member)
        affected.id = 904
        affected.mention = "<@904>"
        occurred_at = datetime.datetime(
            2026, 11, 2, 10, 0, tzinfo=datetime.timezone.utc
        )

        warning = await send_moderation_log(
            store,
            guild,
            action="Banned member",
            actor=actor,
            affected=affected,
            reason="Repeated spam",
            occurred_at=occurred_at,
        )

        self.assertIsNone(warning)
        log_channel.send.assert_awaited_once()
        embed = log_channel.send.await_args.kwargs["embed"]
        fields = {field.name: field.value for field in embed.fields}
        self.assertIn("Banned member", embed.title)
        self.assertIn("903", fields["Actor"])
        self.assertIn("904", fields["Affected member"])
        self.assertEqual(fields["Reason"], "Repeated spam")
        self.assertEqual(embed.timestamp, occurred_at)
        allowed_mentions = log_channel.send.await_args.kwargs["allowed_mentions"]
        self.assertFalse(allowed_mentions.everyone)
        self.assertFalse(allowed_mentions.users)
        self.assertFalse(allowed_mentions.roles)

    async def test_automod_event_is_logged_without_breaking_enforcement(self) -> None:
        log_channel = Mock(spec=discord.TextChannel)
        log_channel.send = AsyncMock()
        guild = Mock(spec=discord.Guild)
        guild.id = 901
        guild.owner_id = 999
        guild.me = None
        guild.get_channel.return_value = log_channel

        member = Mock(spec=discord.Member)
        member.bot = False
        member.id = 903
        member.mention = "<@903>"
        member.guild_permissions = SimpleNamespace(manage_messages=False)
        member.top_role = object()
        source_channel = Mock(spec=discord.TextChannel)
        source_channel.id = 905
        source_channel.send = AsyncMock()
        message = Mock(spec=discord.Message)
        message.guild = guild
        message.author = member
        message.content = "discord.gg/example"
        message.mentions = []
        message.role_mentions = []
        message.mention_everyone = False
        message.channel = source_channel
        message.created_at = datetime.datetime(
            2026, 11, 2, 10, 0, tzinfo=datetime.timezone.utc
        )
        message.delete = AsyncMock()
        store = AsyncMock()
        store.get_settings.side_effect = [
            {
                "automod_enabled": True,
                "automod_block_invites": True,
                "automod_max_mentions": 5,
                "automod_spam_limit": 6,
                "moderation_log_channel_id": 902,
            },
            {"moderation_log_channel_id": 902},
        ]

        enforced = await handle_automod(store, message)

        self.assertTrue(enforced)
        message.delete.assert_awaited_once()
        source_channel.send.assert_awaited_once()
        log_channel.send.assert_awaited_once()
        fields = {
            field.name: field.value
            for field in log_channel.send.await_args.kwargs["embed"].fields
        }
        self.assertEqual(fields["Actor"], "NEXUS V1 AutoMod")
        self.assertIn("903", fields["Affected member"])
        self.assertIn("invite links", fields["Reason"])

    async def test_missing_log_channel_warns_after_clear_succeeds(self) -> None:
        store = AsyncMock()
        store.get_settings.return_value = {"moderation_log_channel_id": 902}
        client = discord.Client(intents=discord.Intents.none())
        client.tree = discord.app_commands.CommandTree(client)
        register_commands(client, store)

        actor = Mock(spec=discord.Member)
        actor.id = 903
        channel = Mock(spec=discord.TextChannel)
        channel.name = "general"
        channel.purge = AsyncMock(return_value=[object(), object()])
        bot_member = SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_messages=True)
        )
        guild = Mock(spec=discord.Guild)
        guild.id = 901
        guild.me = bot_member
        guild.get_channel.return_value = None
        interaction = SimpleNamespace(
            guild=guild,
            user=actor,
            channel=channel,
            response=SimpleNamespace(defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        clear_command = client.tree.get_command("clear")
        assert clear_command is not None

        await clear_command.callback(interaction, amount=2)

        channel.purge.assert_awaited_once()
        response = interaction.followup.send.await_args.args[0]
        self.assertIn("Deleted 2 message(s).", response)
        self.assertIn("missing or inaccessible", response)
        await client.close()


if __name__ == "__main__":
    unittest.main()
