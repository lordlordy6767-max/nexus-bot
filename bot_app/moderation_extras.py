from __future__ import annotations

import datetime

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.moderation import _target_error
from bot_app.storage import BotStore


def register_moderation_extras(
    bot: discord.Client,
    store: BotStore,
) -> None:
    @bot.tree.command(name="warn", description="Record a warning for a member.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(user="Member to warn.", reason="Reason for the warning.")
    async def warn(
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str,
    ) -> None:
        guild = interaction.guild
        actor = interaction.user
        if guild is None or not isinstance(actor, discord.Member):
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return
        error = _target_error(interaction, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        safe_reason = reason.strip()[:500]
        if not safe_reason:
            await interaction.response.send_message(
                "Enter a reason for the warning.",
                ephemeral=True,
            )
            return

        warning_id = await store.add_warning(
            guild.id,
            user.id,
            actor.id,
            safe_reason,
        )
        await interaction.response.send_message(
            embed=brand_embed(
                "Warning recorded",
                f"{user.mention} received warning **#{warning_id}**.\n"
                f"Reason: {safe_reason}",
                color=PURPLE,
            ),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="warnings", description="View a member's active warnings.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(user="Member whose warnings you want to view.")
    async def warnings(
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        warning_count = await store.count_warnings(guild.id, user.id)
        rows = await store.get_warnings(guild.id, user.id, limit=10)
        if not rows:
            await interaction.response.send_message(
                f"{user.display_name} has no active warnings.",
                ephemeral=True,
            )
            return

        lines = []
        for row in rows:
            created = datetime.datetime.fromtimestamp(
                int(row["created_at"]),
                tz=datetime.timezone.utc,
            )
            reason = str(row["reason"]).replace("\n", " ")[:220]
            lines.append(
                f"**#{int(row['warning_id'])}** · "
                f"{discord.utils.format_dt(created, style='d')} · "
                f"<@{int(row['moderator_id'])}>\n{reason}"
            )
        embed = brand_embed(
            f"Active warnings · {user.display_name}",
            "\n\n".join(lines),
            color=PURPLE,
        )
        if warning_count > len(rows):
            embed.set_footer(
                text=f"Showing the 10 most recent of {warning_count} active warnings."
            )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="unwarn", description="Clear one active warning.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(
        user="Member whose warning should be cleared.",
        warn_id="Warning ID shown by /warnings.",
    )
    async def unwarn(
        interaction: discord.Interaction,
        user: discord.Member,
        warn_id: app_commands.Range[int, 1, 9_007_199_254_740_991],
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        cleared = await store.clear_warning(
            guild.id,
            user.id,
            int(warn_id),
            interaction.user.id,
        )
        if not cleared:
            await interaction.response.send_message(
                "That active warning was not found for this member.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Warning **#{warn_id}** for {user.display_name} was cleared.",
            ephemeral=True,
        )

    @bot.tree.command(name="unban", description="Unban a Discord account ID.")
    @app_commands.guild_only()
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user_id="Discord account ID to unban.")
    async def unban(
        interaction: discord.Interaction,
        user_id: str,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        normalized_id = user_id.strip()
        if not normalized_id.isdigit() or len(normalized_id) > 20:
            await interaction.response.send_message(
                "Enter a valid numeric Discord account ID.",
                ephemeral=True,
            )
            return
        target_id = int(normalized_id)
        if target_id <= 0:
            await interaction.response.send_message(
                "Enter a valid numeric Discord account ID.",
                ephemeral=True,
            )
            return
        bot_member = guild.me
        if bot_member is None or not bot_member.guild_permissions.ban_members:
            await interaction.response.send_message(
                "I need the Ban Members permission to do that.",
                ephemeral=True,
            )
            return

        try:
            await guild.unban(
                discord.Object(id=target_id),
                reason=f"NEXUS V1 unban by {interaction.user}",
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "That account is not currently banned from this server.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Account `{target_id}` was unbanned.",
            ephemeral=True,
        )

    @bot.tree.command(name="unmute", description="Remove a member's timeout.")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(user="Member whose timeout should be removed.")
    async def unmute(
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        error = _target_error(interaction, user)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        guild = interaction.guild
        bot_member = guild.me if guild is not None else None
        if bot_member is None or not bot_member.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "I need the Moderate Members permission to do that.",
                ephemeral=True,
            )
            return
        if user.timed_out_until is None:
            await interaction.response.send_message(
                f"{user.display_name} does not have an active timeout.",
                ephemeral=True,
            )
            return
        await user.timeout(
            None,
            reason=f"NEXUS V1 unmute by {interaction.user}",
        )
        await interaction.response.send_message(
            f"The timeout for {user.display_name} was removed.",
            ephemeral=True,
        )
