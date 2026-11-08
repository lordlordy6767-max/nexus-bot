# premium_all.py - USES Nexus_premium.py paywall - DO NOT make a new lock
import json, os, asyncio, random
import discord

# --- USE YOUR EXISTING LOCK ---
# This imports YOUR unlock/lock from Nexus_premium.py
from bot_app.Nexus_premium import check_paywall, is_allowed, is_owner
CONFIG_FILE = "premium_config.json"

def load():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f: return json.load(f)
        except: return {}
    return {}
def save(d):
    with open(CONFIG_FILE, "w") as f: json.dump(d, f, indent=2)
config = load()
def cfg(gid): return config.get(str(gid), {})
def set_cfg(gid, key, val):
    gid=str(gid)
    if gid not in config: config[gid]={}
    config[gid][key]=val; save(config)

# --- 0. FONTS - PREMIUM LOCKED WITH YOUR PAYWALL ---
FONTS = {
    "bold": "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗",
    "italic": "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍",
    "bubble": "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ",
    "small": "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
    "big": "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
    "mono": "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉",
    "cursive": "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
    "flip": "ɐqɔpǝɟɓɥᴉɾʞlɯuodbɹsʇnʌʍxʎz∀ᗺƆᗡƎℲ⅁H̔I̔ſʞ⅂WNOԀΌᴚS⊥∩ΛMX⅄Z",
}
NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
def convert_font(text, font_name):
    font_name = font_name.lower()
    if font_name not in FONTS: return text
    mapping = FONTS[font_name]
    out = ""
    for ch in text:
        if ch in NORMAL:
            idx = NORMAL.index(ch)
            out += mapping[idx] if idx < len(mapping) else ch
        else: out += ch
    return out
def list_fonts():
    return "🎨 **Fonts:** `bold`, `italic`, `bubble`, `small`, `big`, `mono`, `cursive`, `flip`\nUse: `!font bold Hello` / `!big Hello` / `!create categories big Gaming`"
def apply_font_if_any(name, words):
    if len(words) >= 2 and words[0].lower() in FONTS:
        return convert_font(" ".join(words[1:]), words[0].lower())
    return name

# --- 1. AUTO ROLE ---
def set_autorole(gid, rid): set_cfg(gid,"autorole",str(rid)); return f"✅ AutoRole set <@&{rid}>"
def remove_autorole(gid):
    c=cfg(gid); c.pop("autorole",None); config[str(gid)]=c; save(config); return "✅ AutoRole removed"
async def give_autorole(m):
    c=cfg(m.guild.id)
    if "autorole" in c:
        r=m.guild.get_role(int(c["autorole"]))
        if r:
            try: await m.add_roles(r)
            except: pass

# --- 2. LEVEL ROLES ---
def set_level_role(gid, lvl, rid):
    c=cfg(gid); lr=c.get("level_roles",{}); lr[str(lvl)]=str(rid); set_cfg(gid,"level_roles",lr)
    return f"✅ Level {lvl} = <@&{rid}>"
def list_level_roles(gid):
    lr=cfg(gid).get("level_roles",{})
    if not lr: return "No level roles. `!levelrole 10 @VIP`"
    return "🏆 **Level Roles:**\n"+"\n".join([f"Level {k} -> <@&{v}>" for k,v in sorted(lr.items(), key=lambda x: int(x[0]))])
async def check_level_roles(m, lvl):
    lr=cfg(m.guild.id).get("level_roles",{})
    if str(lvl) in lr:
        r=m.guild.get_role(int(lr[str(lvl)]))
        if r and r not in m.roles:
            try: await m.add_roles(r); return r
            except: pass
    return None

# --- 3. AFK ---
def set_afk(gid, uid, reason):
    c=cfg(gid); afk=c.get("afk",{}); afk[str(uid)]=reason; set_cfg(gid,"afk",afk)
def remove_afk(gid, uid):
    c=cfg(gid); afk=c.get("afk",{}); afk.pop(str(uid),None); set_cfg(gid,"afk",afk)
def get_afk(gid, uid): return cfg(gid).get("afk",{}).get(str(uid))

# --- 4. CUSTOM COMMANDS ---
def add_custom_cmd(gid, name, text):
    c=cfg(gid); cmds=c.get("custom_cmds",{}); cmds[name.lower()]=text; set_cfg(gid,"custom_cmds",cmds)
    return f"✅ Custom command `!{name}` created!"
def del_custom_cmd(gid, name):
    c=cfg(gid); cmds=c.get("custom_cmds",{}); cmds.pop(name.lower(),None); set_cfg(gid,"custom_cmds",cmds)
    return f"✅ Deleted `!{name}`"
def get_custom_cmd(gid, name): return cfg(gid).get("custom_cmds",{}).get(name.lower())
def list_custom_cmds(gid):
    cmds=cfg(gid).get("custom_cmds",{})
    if not cmds: return "No custom commands. `!addcmd hello Hello!`"
    return "✨ **Custom Commands:**\n"+"\n".join([f"`!{k}` -> {v[:50]}" for k,v in cmds.items()])

# --- 5. STARBOARD ---
def set_starboard(gid, ch_id, emoji="⭐", count=3):
    set_cfg(gid,"starboard",str(ch_id)); set_cfg(gid,"star_emoji",emoji); set_cfg(gid,"star_count",count)
    return f"✅ Starboard set in <#{ch_id}> - {count}x {emoji} = star!"
async def handle_starboard(reaction, user):
    if user.bot: return
    c=cfg(reaction.message.guild.id)
    if "starboard" not in c: return
    if str(reaction.emoji) != c.get("star_emoji","⭐"): return
    if reaction.count < int(c.get("star_count",3)): return
    ch=reaction.message.guild.get_channel(int(c["starboard"]))
    if not ch: return
    async for m in ch.history(limit=50):
        if str(reaction.message.id) in m.content: return
    embed=discord.Embed(description=reaction.message.content, color=0xFFD700)
    embed.set_author(name=str(reaction.message.author), icon_url=reaction.message.author.display_avatar.url)
    embed.add_field(name="Jump", value=f"[Go to message]({reaction.message.jump_url})")
    await ch.send(f"{c.get('star_emoji','⭐')} {reaction.count} | <#{reaction.message.channel.id}>", embed=embed)

# --- 6. BACKUP ---
async def make_backup(guild):
    data={"name":guild.name,"channels":[],"roles":[],"categories":[]}
    for cat in guild.categories: data["categories"].append(cat.name)
    for ch in guild.text_channels: data["channels"].append({"name":ch.name,"cat":ch.category.name if ch.category else None,"topic":ch.topic})
    for r in guild.roles:
        if not r.is_default(): data["roles"].append({"name":r.name,"color":str(r.color)})
    with open(f"backup_{guild.id}.json","w") as f: json.dump(data,f,indent=2)
    return f"✅ Backup saved! {len(data['channels'])} channels, {len(data['roles'])} roles, {len(data['categories'])} categories."
async def restore_backup(guild):
    try:
        with open(f"backup_{guild.id}.json") as f: data=json.load(f)
    except: return "❌ No backup found. Do `!backup` first."
    made=0
    for r in data["roles"]:
        if discord.utils.get(guild.roles, name=r["name"]) is None:
            try: await guild.create_role(name=r["name"]); made+=1
            except: pass
    for cat_name in data["categories"]:
        if discord.utils.get(guild.categories, name=cat_name) is None:
            try: await guild.create_category(cat_name)
            except: pass
    for ch in data["channels"]:
        if discord.utils.get(guild.text_channels, name=ch["name"]) is None:
            try: await guild.create_text_channel(ch["name"], topic=ch.get("topic")); made+=1
            except: pass
    return f"✅ Restored! Created {made} missing roles/channels from backup of **{data['name']}**"

# --- 7. GIVEAWAY TO ROLE ---
def parse_giveaway_role(text):
    import re
    m=re.search(r"<@&(\d+)>", text)
    role_id=m.group(1) if m else None
    clean=re.sub(r"<@&\d+>","",text).strip()
    return clean, role_id
def is_eligible_for_giveaway(member, role_id):
    if not role_id: return True
    return any(str(r.id)==str(role_id) for r in member.roles)

# --- 8. AI IMAGE ---
async def ai_image_prompt(prompt): return prompt

# --- 9. MASS CREATE ---
async def mass_create(guild, kind, count, base_name):
    made=[]; count=min(int(count), 20)
    for i in range(1, count+1):
        name=f"{base_name}-{i}"
        try:
            if kind=="channels": await guild.create_text_channel(name)
            elif kind=="roles": await guild.create_role(name=name)
            elif kind=="categories": await guild.create_category(name)
            made.append(name)
        except: break
    return f"✅ Mass created {len(made)} {kind}: {', '.join(made)}"

# --- 10. !list ---
def build_list_embed():
    embed = discord.Embed(title="👑 NEXUS - ALL COMMANDS", description="Everything Starr built", color=0x9B59B6)
    embed.add_field(name="🛠️ CREATE / BUILD - PREMIUM", value="`!create channels gaming, chill`\n`!create categories Gaming`\n`!create roles VIP red`\n`!create categories big Gaming`\n`!create roles bold VIP red`", inline=False)
    embed.add_field(name="🔀 MOVE / RENAME / COLOR - PREMIUM", value="`!move #general Gaming`\n`!rename #general new-name`\n`!color @VIP red`", inline=False)
    embed.add_field(name="🎨 FONTS - PREMIUM", value="`!font bold Hello` / `!font bubble Hello`\n`!big Hello` / `!small Hello`\n`!fonts`", inline=False)
    embed.add_field(name="👑 PREMIUM - NEW", value="`!autorole @Member`\n`!levelrole 10 @VIP` / `!levelroles`\n`!addcmd hello Hi` / `!cmds`\n`!starboard #starboard`\n`!backup` / `!restore`\n`!giveawayrole 1h Nitro @VIP`\n`!masscreate channels 10 gaming`\n`!aiimage a dragon`", inline=False)
    embed.add_field(name="🌍 FREE", value="`!translate Hello` / `!afk sleeping`", inline=False)
    embed.add_field(name="🔓 UNLOCK", value="DM Starr to buy. Starr only: `!unlock @user` / `!lock @user`", inline=False)
    embed.set_footer(text="NEXUS by Starr 👑 | Type !list anytime")
    return embed