import time
from collections import defaultdict
import discord
from discord import app_commands
from bot_app.branding import brand_embed

# guild_id -> True/False, guild_id -> set(user_ids)
_enabled = {}
_whitelist = defaultdict(set)
_actions = defaultdict(list)

def _is_nuke(guild_id, user_id):
    now = time.time()
    _actions[user_id].append(now)
    _actions[user_id] = [t for t in _actions[user_id] if now - t < 10]
    return len(_actions[user_id]) >= 3

async def _punish(bot, guild, user_id, reason):
    try:
        member = guild.get_member(user_id)
        if member and member.id != guild.owner_id and member.id != bot.user.id:
            await guild.ban(member, reason=f"ANTI-NUKE: {reason}")
        # find log channel
        for ch in guild.text_channels:
            if "log" in ch.name.lower() or "mod" in ch.name.lower():
                await ch.send(embed=brand_embed("🚨 ANTI-NUKE TRIGGERED", f"<@{user_id}> tried to nuke ({reason}) - AUTO-BANNED"))
                break
    except Exception as e:
        print(f"Antinuke punish failed: {e}")

def register_antinuke(bot: discord.Client) -> None:
    @bot.tree.command(name="antinuke", description="Anti-nuke protection. Staff only.")
    @app_commands.describe(action="enable / disable / status / whitelist / unwhitelist", user="User to whitelist (only for whitelist/unwhitelist)")
    @app_commands.guild_only()
    async def antinuke(interaction: discord.Interaction, action: str, user: discord.Member | None = None):
        await interaction.response.defer(ephemeral=True)

        # Manual admin check - keeps it staff-only WITHOUT hiding it from Discord
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need Administrator to use this.", ephemeral=True)
            return

        gid = interaction.guild.id
        action = action.lower()

        if action == "enable":
            _enabled[gid] = True
            await interaction.followup.send("✅ Anti-nuke **ENABLED** - I will auto-ban anyone who bans/kicks/deletes 3+ things in 10 seconds", ephemeral=True)
        elif action == "disable":
            _enabled[gid] = False
            await interaction.followup.send("❌ Anti-nuke **DISABLED**", ephemeral=True)
        elif action == "status":
            status = "ON 🟢" if _enabled.get(gid, False) else "OFF 🔴"
            wl = ", ".join([f"<@{u}>" for u in _whitelist.get(gid, set())]) or "None"
            await interaction.followup.send(f"**Anti-Nuke:** {status}\n**Whitelisted:** {wl}", ephemeral=True)
        elif action == "whitelist" and user:
            _whitelist[gid].add(user.id)
            await interaction.followup.send(f"✅ {user.mention} whitelisted - will NEVER be auto-banned", ephemeral=True)
        elif action == "unwhitelist" and user:
            _whitelist[gid].discard(user.id)
            await interaction.followup.send(f"❌ {user.mention} removed from whitelist", ephemeral=True)
        else:
            await interaction.followup.send("Use: `/antinuke enable` / `disable` / `status` / `whitelist @user` / `unwhitelist @user`", ephemeral=True)

    @bot.listen("on_guild_channel_delete")
    async def on_channel_delete(channel):
        guild = channel.guild
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if not _enabled.get(guild.id): return
                if entry.user.id in _whitelist.get(guild.id, set()): return
                if entry.user.id == bot.user.id: return
                if _is_nuke(guild.id, entry.user.id):
                    await _punish(bot, guild, entry.user.id, "Deleted 3+ channels fast")
        except: pass

    @bot.listen("on_guild_role_delete")
    async def on_role_delete(role):
        guild = role.guild
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if not _enabled.get(guild.id): return
                if entry.user.id in _whitelist.get(guild.id, set()): return
                if entry.user.id == bot.user.id: return
                if _is_nuke(guild.id, entry.user.id):
                    await _punish(bot, guild, entry.user.id, "Deleted 3+ roles fast")
        except: pass

    @bot.listen("on_member_ban")
    async def on_ban(guild, user):
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if not _enabled.get(guild.id): return
                if entry.user.id in _whitelist.get(guild.id, set()): return
                if entry.user.id == bot.user.id: return
                if _is_nuke(guild.id, entry.user.id):
                    await _punish(bot, guild, entry.user.id, "Banned 3+ members fast")
        except: pass