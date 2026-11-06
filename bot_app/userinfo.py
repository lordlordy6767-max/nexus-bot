import discord
from discord import app_commands

def register_info_commands(bot, store):
    tree = bot.tree

    @tree.command(name="userinfo", description="Show info about a user")
    @app_commands.describe(user="The user to check (leave empty for yourself)")
    async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
        # Get Member, not just User
        member = user or interaction.guild.get_member(interaction.user.id)
        if member is None:
            member = await interaction.guild.fetch_member(interaction.user.id)

        color = member.top_role.color if member.top_role.color.value != 0 else discord.Color.blue()

        embed = discord.Embed(title=f"{member.display_name}'s Info", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Username", value=f"{member} ({member.mention})", inline=False)
        embed.add_field(name="🆔 User ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)

        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        roles.reverse()
        embed.add_field(name=f"🎭 Roles ({len(roles)})", value=", ".join(roles) if roles else "No roles", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @tree.command(name="serverinfo", description="Show info about this server")
    async def serverinfo(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    if guild is None:
        await interaction.followup.send("This command only works in a server, King 👑")
        return

    # Fix for owner being None - fetch it if needed
    owner = guild.owner
    if owner is None:
        try:
            owner = await guild.fetch_member(guild.owner_id)
        except:
            owner = None

    owner_text = owner.mention if owner else f"<@{guild.owner_id}>"

    embed = discord.Embed(title=f"{guild.name} Info", color=discord.Color.blue())
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.add_field(name="👑 Owner", value=owner_text, inline=True)
    embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="👥 Members", value=f"{guild.member_count}", inline=True)
    embed.add_field(name="💬 Channels", value=f"{len(guild.channels)}", inline=True)
    embed.add_field(name="🎭 Roles", value=f"{len(guild.roles)}", inline=True)
    embed.add_field(name="😀 Emojis", value=f"{len(guild.emojis)}", inline=True)
    embed.add_field(name="🚀 Boosts", value=f"{guild.premium_subscription_count or 0} (Level {guild.premium_tier})", inline=True)
    embed.add_field(name="✅ Verification", value=str(guild.verification_level).title(), inline=True)

    await interaction.followup.send(embed=embed)