from __future__ import annotations

import discord


CYAN = discord.Color.from_rgb(0, 255, 255)
PURPLE = discord.Color.from_rgb(139, 92, 246)


def brand_embed(
    title: str,
    description: str | None = None,
    *,
    color: discord.Color = CYAN,
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="NEXUS V1 • Premium Bot")
    return embed
