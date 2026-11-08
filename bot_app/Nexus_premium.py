# Nexus_premium.py - PAID FEATURES ONLY
# Create / Move / Rename / Color are locked. Translate + Chat are free.
import json
import os
import re
import discord

OWNER_ID = 1545810202232885258

# --- PAYWALL - SAVED FOREVER ---
PAID_FILE = "paid_users.json"

def load_paid():
    if os.path.exists(PAID_FILE):
        try:
            with open(PAID_FILE, "r") as f:
                return set(str(x) for x in json.load(f))
        except:
            return set()
    return set()

def save_paid():
    with open(PAID_FILE, "w") as f:
        json.dump(list(paid_users), f)

paid_users = load_paid()

def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

def is_allowed(user_id):
    return is_owner(user_id) or str(user_id) in paid_users

def unlock(user_id, by_id):
    if not is_owner(by_id):
        return "❌ Only Starr can unlock."
    paid_users.add(str(user_id))
    save_paid()
    return f"✅ Unlocked <@{user_id}> - they can now use create/move."

def lock(user_id, by_id):
    if not is_owner(by_id):
        return "❌ Only Starr can lock."
    paid_users.discard(str(user_id))
    save_paid()
    return f"🔒 Locked <@{user_id}>."

def check_paywall(user_id):
    if is_allowed(user_id):
        return None
    return "🔒 This is NEXUS Premium. Pay Starr to unlock create/move. DM Starr to buy."

# --- HELPERS ---
def clean_channel_name(name):
    name = name.strip().lstrip("#")
    name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
    name = name.strip().lower().replace(" ", "-")
    name = re.sub(r'-+', '-', name)
    return name or "general"

def parse_list(text):
    if not text:
        return []
    quoted = re.findall(r'"([^"]+)"', text)
    text_no_quoted = re.sub(r'"[^"]+"', '', text)
    if "," in text_no_quoted:
        parts = text_no_quoted.split(",")
    else:
        parts = text_no_quoted.split()
    result = [p.strip().lstrip("#").strip() for p in parts if p.strip()]
    result.extend(quoted)
    return [p for p in result if p]

def find_channel(guild, query):
    query = query.strip()
    m = re.search(r'<#(\d+)>', query)
    if m:
        ch = guild.get_channel(int(m.group(1)))
        if ch:
            return ch
    if query.isdigit():
        ch = guild.get_channel(int(query))
        if ch:
            return ch
    clean = query.lstrip("#").lower()
    clean_dash = clean.replace(" ", "-")
    for c in guild.channels:
        if c.name.lower() == clean or c.name.lower() == clean_dash:
            return c
    return None

def find_category(guild, query):
    query = query.strip()
    m = re.search(r'<#(\d+)>', query)
    if m:
        cat = guild.get_channel(int(m.group(1)))
        if cat:
            return cat
    if query.isdigit():
        cat = guild.get_channel(int(query))
        if cat:
            return cat
    clean = query.lstrip("#").lower()
    for c in guild.categories:
        if c.name.lower() == clean:
            return c
    for c in guild.categories:
        if clean in c.name.lower() or c.name.lower() in clean:
            return c
    return None

# --- COLORS ---
COLORS = {
    "red": 0xFF0000, "blue": 0x0000FF, "green": 0x00FF00, "yellow": 0xFFFF00,
    "purple": 0x800080, "pink": 0xFF69B4, "orange": 0xFFA500, "black": 0x000000,
    "white": 0xFFFFFF, "cyan": 0x00FFFF, "gold": 0xFFD700, "silver": 0xC0C0C0,
    "brown": 0x8B4513, "lime": 0x00FF00, "navy": 0x000080, "teal": 0x008080,
    "magenta": 0xFF00FF, "violet": 0xEE82EE, "maroon": 0x800000, "olive": 0x808000,
}

def parse_color(text):
    text = text.strip().lower().lstrip("#")
    if text in COLORS:
        return discord.Color(COLORS[text])
    try:
        return discord.Color(int(text, 16))
    except:
        return None

# --- CREATE ---
async def create_channels(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        clean = clean_channel_name(name)
        ch = await guild.create_text_channel(clean)
        made.append(f"#{ch.name}")
    return f"✅ Created channels: {', '.join(made)}"

async def create_categories(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        display = name.strip().lstrip("#")
        cat = await guild.create_category(display)
        made.append(cat.name)
    return f"✅ Created categories: {', '.join(made)}"

async def create_roles(guild, names_text):
    # Supports: "vip, admin" AND "vip red, admin blue" AND "vip #FF0000"
    parts = parse_list(names_text)
    made = []
    for part in parts:
        words = part.split()
        name = words[0].strip().lstrip("#")
        color = None
        if len(words) > 1:
            color = parse_color(words[1])
        if color:
            role = await guild.create_role(name=name, colour=color)
        else:
            role = await guild.create_role(name=name)
        made.append(role.name)
    return f"✅ Created roles: {', '.join(made)}"

async def create_voice(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        clean = clean_channel_name(name)
        ch = await guild.create_voice_channel(clean)
        made.append(f"#{ch.name}")
    return f"✅ Created voice: {', '.join(made)}"

# --- MOVE ---
async def move_channels(guild, channels_text, category_name):
    category = find_category(guild, category_name)
    if not category:
        return f"❌ Category '{category_name}' not found."
    channel_names = parse_list(channels_text)
    moved = []
    not_found = []
    for ch_name in channel_names:
        ch = find_channel(guild, ch_name)
        if ch:
            await ch.edit(category=category)
            moved.append(f"#{ch.name}")
        else:
            not_found.append(ch_name)
    if not moved:
        return f"❌ No channels found to move. Tried: {', '.join(channel_names)}"
    msg = f"✅ Moved {', '.join(moved)} to {category.name}"
    if not_found:
        msg += f"\n⚠️ Not found: {', '.join(not_found)}"
    return msg

# --- RENAME + COLOR - NEW ---
async def set_role_color(guild, role_name, color_text):
    role = next((r for r in guild.roles if r.name.lower() == role_name.lower().lstrip("#")), None)
    if not role:
        return f"❌ Role '{role_name}' not found."
    color = parse_color(color_text)
    if not color:
        return f"❌ Color '{color_text}' not found. Try: red, blue, green, gold, pink or hex like FF0000"
    await role.edit(colour=color)
    return f"✅ Role {role.mention} color changed to {color_text}!"

async def rename_channel(guild, old_name, new_name):
    ch = find_channel(guild, old_name)
    if not ch:
        return f"❌ Channel '{old_name}' not found."
    if str(ch.type) == "category":
        await ch.edit(name=new_name.strip().lstrip("#"))
    else:
        await ch.edit(name=clean_channel_name(new_name))
    return f"✅ Renamed to {new_name}"

async def rename_category(guild, old_name, new_name):
    cat = find_category(guild, old_name)
    if not cat:
        return f"❌ Category '{old_name}' not found."
    await cat.edit(name=new_name.strip().lstrip("#"))
    return f"✅ Renamed category {cat.name} -> {new_name}"