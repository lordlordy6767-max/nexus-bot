import os
from supabase import create_client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(URL, KEY) if URL and KEY else None

def _default(guild_id, user_id):
    return {"guild_id": str(guild_id), "user_id": str(user_id), "balance": 0, "messages": 0, "xp": 0, "level": 0, "daily_last": 0}

async def get_user(guild_id, user_id):
    if not supabase: return _default(guild_id, user_id)
    res = supabase.table("user_stats").select("*").eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
    if res.data:
        return res.data[0]
    supabase.table("user_stats").insert(_default(guild_id, user_id)).execute()
    return _default(guild_id, user_id)

# ===== ECONOMY =====
async def get_bal(guild_id, user_id):
    user = await get_user(guild_id, user_id)
    return user.get("balance", 0)

async def get_balance(guild_id, user_id):
    return await get_bal(guild_id, user_id)

async def add(guild_id, user_id, amount):
    user = await get_user(guild_id, user_id)
    new_bal = user.get("balance", 0) + amount
    supabase.table("user_stats").update({"balance": new_bal}).eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
    return new_bal

async def add_balance(guild_id, user_id, amount):
    return await add(guild_id, user_id, amount)

async def get_daily_last(guild_id, user_id):
    user = await get_user(guild_id, user_id)
    return user.get("daily_last", 0) or 0

async def set_daily(guild_id, user_id, timestamp):
    await get_user(guild_id, user_id)
    supabase.table("user_stats").update({"daily_last": timestamp}).eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()

# ===== LEVELS + MESSAGES =====
async def get_xp(guild_id, user_id):
    user = await get_user(guild_id, user_id)
    return user.get("xp", 0)

async def add_xp(guild_id, user_id, amount):
    # This is called on every message - +XP AND +1 message
    user = await get_user(guild_id, user_id)
    new_xp = user.get("xp", 0) + amount
    new_level = int((max(0, new_xp) / 100) ** 0.5)  # Same formula as levels.py
    supabase.table("user_stats").update({
        "messages": user.get("messages", 0) + 1,
        "xp": new_xp,
        "level": new_level
    }).eq("guild_id", str(guild_id)).eq("user_id", str(user_id)).execute()
    return new_xp

async def get_messages(guild_id, user_id):
    user = await get_user(guild_id, user_id)
    return user.get("messages", 0)

# ===== LEADERBOARD / RANK =====
async def get_leaderboard(guild_id, limit=10):
    res = supabase.table("user_stats").select("*").eq("guild_id", str(guild_id)).order("xp", desc=True).limit(limit).execute()
    rows = res.data or []
    # levels.py expects "total_xp", your table has "xp" - map it
    for r in rows:
        r["total_xp"] = r.get("xp", 0)
    return rows