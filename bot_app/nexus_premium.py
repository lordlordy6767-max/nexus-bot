# Nexus_premium.py - PAID FEATURES ONLY
# Create / Move are locked. Translate + Chat are free.
import json
import os

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
def parse_list(text):
    # "memes, clips, 💬-general" -> ["memes", "clips", "💬-general"]
    # Also supports "memes clips" or "memes,clips"
    if "," in text:
        parts = text.split(",")
    else:
        parts = text.split()
    return [p.strip() for p in parts if p.strip()]

# --- CREATE ---
async def create_channels(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        ch = await guild.create_text_channel(name)
        made.append(ch.name)
    return f"✅ Created channels: {', '.join(made)}"

async def create_categories(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        cat = await guild.create_category(name)
        made.append(cat.name)
    return f"✅ Created categories: {', '.join(made)}"

async def create_roles(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        role = await guild.create_role(name=name)
        made.append(role.name)
    return f"✅ Created roles: {', '.join(made)}"

async def create_voice(guild, names_text):
    names = parse_list(names_text)
    made = []
    for name in names:
        ch = await guild.create_voice_channel(name)
        made.append(ch.name)
    return f"✅ Created voice: {', '.join(made)}"

# --- MOVE ---
async def move_channels(guild, channels_text, category_name):
    category = next((c for c in guild.categories if c.name.lower() == category_name.lower()), None)
    if not category:
        return f"❌ Category '{category_name}' not found."
    channel_names = parse_list(channels_text)
    moved = []
    for ch_name in channel_names:
        ch = next((c for c in guild.channels if c.name.lower() == ch_name.lower()), None)
        if ch:
            await ch.edit(category=category)
            moved.append(ch.name)
    if not moved:
        return "❌ No channels found to move."
    return f"✅ Moved {', '.join(moved)} to {category.name}"