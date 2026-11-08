# Nexus_premium.py - PAID FEATURES ONLY
# Create / Move are locked. Translate + Chat are free.
import json
import os
import re

OWNER_ID = 1545810202232885258

# --- PAYWALL - SAVED FOREVER ---
# Saves unlocked users to a file so they stay unlocked after restart
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
    # You = always free. Others = only if you unlocked them
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
    # Use this at start of every premium command
    if is_allowed(user_id):
        return None  # allowed, continue
    return "🔒 This is NEXUS Premium. Pay Starr to unlock create/move. DM Starr to buy."

# --- HELPERS ---
def clean_channel_name(name):
    """Discord text/voice channel names: lowercase, no spaces, no emoji, - instead of space"""
    # Remove # at start if user typed #general
    name = name.strip().lstrip("#")
    # Remove emoji / special chars, keep letters, numbers, -, _
    name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
    name = name.strip().lower().replace(" ", "-")
    name = re.sub(r'-+', '-', name)
    return name or "general"

def parse_list(text):
    # "memes, clips, general" -> ["memes", "clips", "general"]
    # Also supports "memes clips", "#memes #clips", "memes,clips"
    # Also supports quoted: "my channel", "cool clips"
    if not text:
        return []
    # Keep quoted names together: "my channel" -> one item
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
    """Find channel by #mention, ID, or name. Handles <#123456> and #general and general"""
    query = query.strip()
    # 1. Discord mention format: <#123456789>
    m = re.search(r'<#(\d+)>', query)
    if m:
        ch = guild.get_channel(int(m.group(1)))
        if ch:
            return ch
    # 2. Pure ID
    if query.isdigit():
        ch = guild.get_channel(int(query))
        if ch:
            return ch
    # 3. Name - remove # and clean
    clean = query.lstrip("#").lower()
    clean_dash = clean.replace(" ", "-")
    for c in guild.channels:
        if c.name.lower() == clean or c.name.lower() == clean_dash:
            return c
    return None

def find_category(guild, query):
    """Find category by #mention, ID, or name"""
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
    # Also try partial match
    for c in guild.categories:
        if clean in c.name.lower() or c.name.lower() in clean:
            return c
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
        # Categories CAN have emoji + spaces, so keep original name (just remove #)
        display = name.strip().lstrip("#")
        cat = await guild.create_category(display)
        made.append(cat.name)
    return f"✅ Created categories: {', '.join(made)}"

async def create_roles(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        display = name.strip().lstrip("#")
        role = await guild.create_role(name=display)
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