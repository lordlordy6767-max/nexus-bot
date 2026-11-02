from __future__ import annotations

import random
import time

import discord
from discord import app_commands

from bot_app.branding import PURPLE, brand_embed
from bot_app.storage import BotStore

_XP_COOLDOWN_SECONDS = 60
_last_xp_award: dict[tuple[int, int], float] = {}


def level_for_xp(total_xp: int) -> int:
    return int((max(0, total_xp) / 100) ** 0.5)


def next_level_xp(level: int) -> int:
    return (level + 1) ** 2 * 100


async def handle_level_message(
    store: BotStore,
    message: discord.Message,
) -> None:
    guild = message.guild
    member = message.author
    if guild is None or not isinstance(member, discord.Member) or member.bot:
        return

    now = time.monotonic()
    key = (guild.id, member.id)
    last_award = _last_xp_award.get(key, 0)
    if now - last_award < _XP_COOLDOWN_SECONDS:
        return
    _last_xp_award[key] = now

    previous_xp = await store.get_xp(guild.id, member.id)
    new_xp = await store.add_xp(
        guild.id,
        member.id,
        random.randint(15, 25),
    )
    old_level = level_for_xp(previous_xp)
    new_level = level_for_xp(new_xp)
    if new_level <= old_level:
        return

    try:
        await message.channel.send(
            embed=brand_embed(
                "Level up!",
                f"{member.mention} reached **Level {new_level}**.",
                color=PURPLE,
            ),
            delete_after=15,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )
    except (discord.Forbidden, discord.HTTPException):
        pass


def register_levels(bot: discord.Client, store: BotStore) -> None:
    @bot.tree.command(name="rank", description="View a member's NEXUS level.")
    @app_commands.guild_only()
    async def rank(
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        subject = member or interaction.user
        total_xp = await store.get_xp(guild.id, subject.id)
        level = level_for_xp(total_xp)
        current_level_xp = level * level * 100
        target_xp = next_level_xp(level)
        progress_xp = max(0, total_xp - current_level_xp)
        needed_xp = max(1, target_xp - current_level_xp)
        progress_percent = min(100, round(progress_xp / needed_xp * 100))

        embed = brand_embed(
            f"{subject.display_name}'s Rank",
            f"**Level:** {level}\n"
            f"**XP:** {total_xp:,}\n"
            f"**Next level:** {progress_xp:,} / {needed_xp:,} XP "
            f"({progress_percent}%)",
            color=PURPLE,
        )
        embed.set_thumbnail(url=subject.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(
        name="leaderboard",
        description="Show this server's top NEXUS members.",
    )
    @app_commands.guild_only()
    async def leaderboard(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            return
        rows = await store.get_leaderboard(guild.id, limit=10)
        if not rows:
            await interaction.response.send_message(
                "No one has earned XP yet. Chat to get on the leaderboard!",
                ephemeral=True,
            )
            return

        lines = []
        for place, row in enumerate(rows, start=1):
            user_id = int(row["user_id"])
            total_xp = int(row["total_xp"])
            member = guild.get_member(user_id)
            display_name = member.display_name if member else f"<@{user_id}>"
            lines.append(
                f"**{place}.** {display_name} — Level "
                f"{level_for_xp(total_xp)} · {total_xp:,} XP"
            )

        embed = brand_embed(
            "NEXUS V1 Leaderboard",
            "\n".join(lines),
            color=PURPLE,
        )
        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )
