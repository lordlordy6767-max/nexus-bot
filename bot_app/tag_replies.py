import discord
import random

OWNER_ID = 1545810202232885258  # starrlightz - ONLY YOU can use stats

TRUTHS = [
    "What's the most embarrassing thing you've ever done?",
    "Who's your secret crush right now?",
    "What's the biggest lie you've ever told?",
    "What's the weirdest thing you've searched on your phone?",
    "Have you ever stalked an ex on socials? Be honest 👀",
    "What's the most cringe DM you've ever sent?",
]
DARES = [
    "Send the last photo in your camera roll to this chat 📸",
    "Change your nickname to 'Nexus owns me' for 10 minutes",
    "Send a voice note singing the chorus of any song 🎤",
    "Do your best impression of someone in this server",
    "Text 'hey' to the 3rd person in your recent DMs and screenshot it",
]
QUOTES = [
    "Don't chase. Attract. - Nexus 👑",
    "Move in silence, let results make noise.",
    "Kings don't beg for a seat. They build the table.",
]
HYPES = [
    "Certified LEGEND. No debate 👑",
    "Main character energy only. Everyone else is background.",
    "Too clean. Too real. Too dangerous 🔥",
    "If aura was a person, it would be you.",
]

# --- NEW HELPERS FOR LOVE / GENDER ---
def get_gender(member):
    if member is None:
        return "unknown"
    role_names = [r.name.lower() for r in member.roles]
    if "female" in role_names or "girl" in role_names or "she" in role_names or "queen" in role_names:
        return "female"
    if "male" in role_names or "boy" in role_names or "he" in role_names or "king" in role_names:
        return "male"
    return "unknown"

def get_random_member(message, bot):
    members = [m for m in message.guild.members if not m.bot]
    nexus = discord.utils.get(message.guild.members, name="Nexus")
    if nexus and nexus not in members:
        members.append(nexus)
    return random.choice(members) if members else message.author

def get_opposite_gender_member(message, target_user):
    target_gender = get_gender(target_user)
    if target_gender == "unknown":
        return get_random_member(message, None)
    wanted = "female" if target_gender == "male" else "male"
    candidates = []
    for m in message.guild.members:
        if m.bot and m.name != "Nexus":
            continue
        if m.id == target_user.id:
            continue
        if get_gender(m) == wanted:
            candidates.append(m)
    if not candidates:
        return get_random_member(message, None)
    return random.choice(candidates)

async def handle_tag_reply(bot, message: discord.Message) -> bool:
    if message.author.bot:
        return False
    if bot.user is None:
        return False
    if bot.user not in message.mentions:
        return False

    text = message.content.lower()
    author = message.author
    targets = [m for m in message.mentions if m.id != bot.user.id]
    target = targets[0] if targets else None
    target2 = targets[1] if len(targets) > 1 else None
    target_mention = target.mention if target else author.mention

# LIST - Show all tag commands
    if "list" in text or "commands" in text:
        await message.reply(
            "**What you can say after tagging me:**\n\n"
            "**👑 KING:**\n"
            "`who is the king` • `who is the goat` • `who is your developer` • `praise @user` • `crown @user`\n\n"
            "**🔥 COOK / ROAST:**\n"
            "`cook @user` • `roast @user` • `rate @user` • `expose @user` • `cancel @user` • `hype @user`\n\n"
            "**❤️ LOVE:**\n"
            "`love you` • `hug @user` • `kiss @user` • `ship @user @user` • `marry @user` • `marry me` • `who is @user soulmate` • `who will @user marry`\n\n"
            "**🥊 FIGHT:**\n"
            "`fight @user` • `slap @user` • `vs @user` • `jumpscare @user` • `bonk @user` • `bite @user` • `lick @user` • `kill @user` • `arrest @user` • `jail @user`\n\n"
            "**✨ AURA / RIZZ:**\n"
            "`aura @user` • `who has the most aura` • `who has aura` • `rizz @user` • `vibe check @user` • `how gay is @user` • `how smart is @user` • `how rich is @user` • `iq @user` • `dumbest @user` • `smartest @user` • `pat @user`\n\n"
            "**🔮 PREDICT:**\n"
            "`predict @user` • `fortune @user` • `when will @user get married` • `when will @user get rich`\n\n"
            "**🎲 GAME / LUCK:**\n"
            "`coinflip` • `dice` • `8ball` • `truth or dare @user` • `truth @user` • `dare @user` • `pick pizza or burger`\n\n"
            "**😂 SERVER SUPERLATIVES:**\n"
            "`who is the funniest` • `who is the biggest yapper` • `who yaps the most`\n\n"
            "**🎤 MUSIC / FUN:**\n"
            "`sing` • `sing for @user` • `rap @user` • `quote` • `hype @user`\n\n"
            "**📖 STORY TIME:**\n"
            "`tell me a story` • `tell me a spooky story` • `tell me a sweet story` • `tell me a funny story` • `tell me a motivational story` • `story time`\n\n"
            "**👤 INFO:**\n"
            "`who is @user` • `avatar @user` • `joined @user` • `message @user`\n\n"
            "**🤖 BOT:**\n"
            "`are you real` • `are you smart` • `ping` • `hello`\n\n"
            "Or use `/help` for ALL commands!"
        )
        return True

    # --- OWNER ONLY STATS ---
    elif "stats" in text:
        if message.author.id != OWNER_ID:
            await message.reply("Nah, this one is King-only 👑")
            return True
        total_servers = len(bot.guilds)
        total_users = sum(g.member_count or 0 for g in bot.guilds)
        server_list = "\n".join([f"- {g.name} ({g.member_count} members)" for g in bot.guilds[:10]])
        await message.reply(f"📊 **Nexus Stats**\nServers: **{total_servers}**\nTotal Users: **{total_users}**\n\nTop Servers:\n{server_list}")
        return True

    # --- NEW: TRUTH OR DARE ---
    elif "truth or dare" in text:
        if not target:
            await message.reply("Tag someone King! Like: `@Nexus truth or dare @Friend`")
        else:
            if random.choice([True, False]):
                await message.reply(f"{target_mention} - **TRUTH** 👀\n{random.choice(TRUTHS)}\n\nYou have to answer, no skipping!")
            else:
                await message.reply(f"{target_mention} - **DARE** 🔥\n{random.choice(DARES)}\n\nDo it or you're scared 😈")
        return True
    elif text.strip().endswith("truth") or " truth " in text or "truth @" in text:
        if target:
            await message.reply(f"{target_mention} - **TRUTH** 👀\n{random.choice(TRUTHS)}")
            return True
    elif " dare " in text or text.strip().endswith("dare") or "dare @" in text:
        if target:
            await message.reply(f"{target_mention} - **DARE** 🔥\n{random.choice(DARES)}")
            return True
    elif "hype" in text:
        await message.reply(f"{target_mention} {random.choice(HYPES)}")
        return True
    elif "quote" in text:
        await message.reply(f"\"{random.choice(QUOTES)}\"")
        return True
    elif "pick" in text and " or " in text:
        parts = text.split("pick", 1)[1].strip().split(" or ")
        if len(parts) >= 2:
            await message.reply(f"I pick **{random.choice(parts).strip()}** 👑 No debate.")
            return True

    # --- DEVELOPER ---
    elif "who is your developer" in text or "who made you" in text or "who created you" in text or "who is your creator" in text:
        await message.reply("My developer is **starrlightz** 👑 The GOAT. The legend. No debate! 🐐🔥")
    elif "who is the king" in text:
        await message.reply("My developer, obviously 👑 No debate!")
    elif "who is the goat" in text:
        await message.reply("My developer. No debate. The GOAT 🐐👑")
    elif "praise" in text:
        await message.reply(f"Everyone bow down 🙇 {target_mention} is LEGENDARY. Certified by NEXUS 👑🔥")
    elif "crown" in text:
        await message.reply(f"👑 CROWNING {target_mention} as KING/QUEEN of this server! All hail! 👑")
    elif "cook" in text:
        cooks = [
            f"{target_mention} got COOKED 💀🍳 No comeback, just take the L.",
            f"{target_mention} just got cooked so hard even Gordon Ramsay felt it 🔥",
            f"Someone call the fire department, {target_mention} is BURNT 🍳💀",
            f"{target_mention} got cooked, seasoned, and served. Dinner is ready 😭",
        ]
        await message.reply(random.choice(cooks))
    elif "roast" in text:
        roasts = [
            f"{target_mention} You're so slow, you make a turtle look like Flash 💀",
            f"{target_mention} You have the personality of a loading screen 💀",
            f"{target_mention} Even my code has fewer bugs than your comebacks 💀",
            f"{target_mention} You're the reason why the WiFi goes down 💀",
            f"{target_mention} I'd roast you more but my developer told me to be nice... barely 😭",
            f"{target_mention} You bring everyone so much joy... when you leave the VC 💀",
        ]
        await message.reply(random.choice(roasts))
    elif "rate" in text:
        score = random.randint(1, 10)
        await message.reply(f"{target_mention} I rate you **{score}/10** {'🔥 LEGENDARY' if score >= 9 else '😭 tough' if score <= 3 else '👍 solid'}")
    elif "expose" in text:
        exposes = [
            f"🚨 EXPOSED: {target_mention} still watches cartoons at 3AM 👀",
            f"🚨 EXPOSED: {target_mention} screenshots everything in this server 👀",
            f"🚨 EXPOSED: {target_mention} types... then deletes... then types again 😭",
            f"🚨 EXPOSED: {target_mention} has 47 unread DMs they ignore 👀",
        ]
        await message.reply(random.choice(exposes))
    elif "cancel" in text:
        await message.reply(f"🚫 {target_mention} has been CANCELLED. Pack your bags. It's over. 💀")
    elif "ship" in text:
        if target and target2:
            pct = random.randint(0, 100)
            await message.reply(f"💘 Shipping {target.mention} x {target2.mention} = **{pct}%** match! {'PERFECT COUPLE 💍' if pct >= 80 else '...maybe just friends 😭' if pct < 30 else 'Could work 👀'}")
        else:
            await message.reply("Tag 2 people! Like: `@NEXUS ship @user1 @user2` 💘")
    elif "hug" in text:
        await message.reply(f"🤗 {author.mention} gives {target_mention} a BIG hug! Wholesome moment 🥹❤️")
    elif "kiss" in text:
        await message.reply(f"😘 {author.mention} kisses {target_mention}... OKAY GET A ROOM 😭❤️")
    # --- NEW: SOULMATE + WHO WILL MARRY (GENDER AWARE) - MUST BE BEFORE GENERIC MARRY ---
    elif "soulmate" in text:
        user = target if target else author
        soul = get_opposite_gender_member(message, user)
        await message.reply(f"{user.mention}'s soulmate is {soul.mention} ❤️")
    elif "who will" in text and "marry" in text:
        user = target if target else author
        partner = get_opposite_gender_member(message, user)
        verb = random.choice(["will", "may", "might"])
        await message.reply(f"{user.mention} {verb} marry {partner.mention}, do you agree? Yes/No")
    elif "marry" in text:
        if "marry me" in text:
            await message.reply(f"Sorry {author.mention} 💍 I'm already married to the grind. My developer said no.")
        else:
            await message.reply(f"💍 {author.mention} proposes to {target_mention}! Say YES! 💍❤️")
    elif "love you" in text or "i love you" in text:
        await message.reply(f"Aww {author.mention} ❤️ I love you too, but my developer is my #1")
    elif "fight" in text:
        winner = random.choice([author.mention, target_mention])
        await message.reply(f"🥊 {author.mention} VS {target_mention}... FIGHT! *intense battle*... AND THE WINNER IS {winner}!! 🏆")
    elif "slap" in text:
        await message.reply(f"👋 *SLAP!* {author.mention} slapped {target_mention} so hard their WiFi disconnected 💀")
    elif "vs" in text:
        await message.reply(f"⚔️ {author.mention} VS {target_mention} - Who wins? My money is on {random.choice([author.mention, target_mention])} 🔥")
    elif "jumpscare" in text:
        await message.reply(f"BOO!! 😱👻 {target_mention} JUST GOT JUMPSCARED! Did you drop your phone? 😂")
    elif "bonk" in text:
        await message.reply(f"🔨 BONK! {author.mention} bonks {target_mention} on the head. Go to horny jail 😭")
    elif "pat" in text:
        await message.reply(f"🥹 {author.mention} pats {target_mention} on the head. Good boy/girl ❤️")
    elif "bite" in text:
        await message.reply(f"🦷 CHOMP! {author.mention} bites {target_mention}! That left a mark 😭")
    elif "lick" in text:
        await message.reply(f"👅 {author.mention} licks {target_mention}... BRO WHY 😭😭 That's disgusting!")
    elif "kill" in text:
        await message.reply(f"💀 {author.mention} eliminated {target_mention}! RIP. F in chat 🪦😭")
    elif "arrest" in text:
        await message.reply(f"🚨🚔 {author.mention} ARRESTS {target_mention}! You have the right to remain silent... and cringe. Hands up! 🚨")
    elif "jail" in text:
        await message.reply(f"🔒 {target_mention} has been sent to JAIL for being too sus. No bail. 🚔💀")
    elif "vibe check" in text:
        score = random.randint(0, 100)
        await message.reply(f"✨ VIBE CHECK for {target_mention}: **{score}%** {'IMMACULATE VIBES 🔥' if score >= 80 else 'Vibes are OFF 😭' if score < 30 else 'Mid vibes 👀'}")
    # --- NEW: WHO HAS MOST AURA / FUNNIEST / BIGGEST YAPPER - MUST BE BEFORE GENERIC AURA ---
    elif "who has" in text and "aura" in text:
        winner = get_random_member(message, bot)
        aura = random.randint(100, 10000)
        await message.reply(f"{winner.mention} has the most aura in this server! ✨ {aura} aura")
    elif "funniest" in text:
        winner = get_random_member(message, bot)
        await message.reply(f"{winner.mention} is the funniest in this server 😂")
    elif "biggest yapper" in text or "yaps the most" in text or "biggest yap" in text:
        winner = get_random_member(message, bot)
        await message.reply(f"{winner.mention} never stops yapping 💀 Biggest yapper in this server!")
    elif "aura" in text:
        aura = random.randint(-1000, 10000)
        await message.reply(f"✨ {target_mention} has **{aura} aura** {'👑 AURA FARMER' if aura > 5000 else '💀 NEGATIVE AURA' if aura < 0 else 'Solid aura 👍'}")
    elif "rizz" in text:
        rizz = random.randint(0, 100)
        await message.reply(f"😏 {target_mention} has **{rizz}% RIZZ** {'RIZZLER OF THE CENTURY 🔥' if rizz >= 90 else 'No rizz. Zero. None. 😭' if rizz < 20 else 'Some rizz 👀'}")
    elif "how gay" in text:
        pct = random.randint(0, 100)
        await message.reply(f"🏳️‍🌈 {target_mention} is **{pct}% gay** {'Certified 😭' if pct >= 80 else 'Straight as a ruler 📏' if pct < 20 else 'A little sus 👀'}")
    elif "how smart" in text:
        pct = random.randint(0, 100)
        await message.reply(f"🧠 {target_mention} is **{pct}% smart** {'EINSTEIN LEVEL 🤯' if pct >= 90 else '...Google is your friend 😭' if pct < 20 else 'Average brain 🧠'}")
    elif "how rich" in text:
        pct = random.randint(0, 100)
        await message.reply(f"💰 {target_mention} is **{pct}% rich** {'BILLIONAIRE 💸' if pct >= 90 else 'Broke bestie 😭' if pct < 20 else 'Doing okay 💵'}")
    elif "iq" in text:
        iq = random.randint(40, 200)
        await message.reply(f"🧠 {target_mention}'s IQ is **{iq}** {'GENIUS 🤯' if iq >= 140 else '...lets not talk about it 😭' if iq < 70 else 'Normal human 👍'}")
    elif "dumbest" in text:
        await message.reply(f"🤡 The dumbest person here is... {target_mention}! No offense... actually full offense 💀")
    elif "smartest" in text:
        await message.reply(f"🧠 The smartest person here is... {target_mention}! Big brain energy! 🤯👑")
    elif "predict" in text:
        preds = [
            f"🔮 I predict {target_mention} will become FAMOUS in 2027!",
            f"🔮 I predict {target_mention} will get rich... or get scammed. 50/50 😭",
            f"🔮 I predict {target_mention} will meet their soulmate very soon 👀❤️",
            f"🔮 I predict {target_mention} will fail their next exam... unless they study 😭",
        ]
        await message.reply(random.choice(preds))
    elif "fortune" in text:
        fortunes = [
            f"🥠 Fortune for {target_mention}: Good luck is coming your way!",
            f"🥠 Fortune for {target_mention}: Someone in this server likes you 👀",
            f"🥠 Fortune for {target_mention}: Don't trust the person reading this over your shoulder 😭",
            f"🥠 Fortune for {target_mention}: Your crush will text you soon... maybe.",
        ]
        await message.reply(random.choice(fortunes))
    # --- NEW: WHEN WILL GET RICH - MUST BE BEFORE WHEN WILL MARRIED ---
    elif "when will" in text and "get rich" in text:
        user = target if target else author
        months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        month = random.choice(months)
        year = random.randint(2027, 2045)
        await message.reply(f"{user.mention} will get rich in {month} {year}! Start saving 💰")
    elif "when will" in text and "married" in text:
        year = random.randint(2027, 2045)
        await message.reply(f"💍 {target_mention} will get married in **{year}**! Start saving for the wedding 😭💍")
    elif "coinflip" in text or "coin flip" in text:
        await message.reply(f"🪙 Coinflip... It's **{random.choice(['HEADS', 'TAILS'])}**!")
    elif "dice" in text:
        await message.reply(f"🎲 {author.mention} rolled a **{random.randint(1, 6)}**!")
    elif "8ball" in text or "8 ball" in text or "eight ball" in text:
        answers = ["Yes 🔥", "No 💀", "Maybe 👀", "Definitely!", "Ask again later 😭", "100% YES", "Nah bro 💀", "My developer says yes 👑"]
        await message.reply(f"🎱 Magic 8-Ball says: **{random.choice(answers)}**")
    elif "sing for" in text:
        await message.reply(f"🎤 *singing for {target_mention}* La la laaa... You're beautiful, you're amazing, you're... okay I'm done 😭🎤")
    elif "rap" in text:
        await message.reply(f"🎤 Yo yo yo, {target_mention} in the house, so fresh so clean, best in the server, know what I mean? 🔥🎤 Mic drop.")
    elif "sing" in text:
        await message.reply("🎤 La la laaa... I sing better than your favorite artist, no cap 🔥")
    elif "are you real" in text:
        await message.reply("Realer than your last relationship 😭 I'm NEXUS V1, built different 🤖")
    elif "are you smart" in text:
        await message.reply("Smarter than you, and I was built in a few days 😎🧠")
    elif "help" in text:
        await message.reply(f"Need help {author.mention}? Use `/help` to see all commands! Or tag me + `list`")
    elif "ping" in text:
        await message.reply("Pong! 🏓")
    elif any(w in text for w in ["hello", "hi", "hey", "yo"]):
        await message.reply(f"Hello {author.mention}! Welcome to the future. 🔥")
    elif "message" in text or "messages" in text:
        count = 0
        try:
            import json, os
            if os.path.exists("message_counts.json"):
                with open("message_counts.json") as f:
                    data = json.load(f)
                    count = data.get(str(message.guild.id), {}).get(str(target.id), 0)
        except:
            count = 0
        await message.reply(f"💬 {target_mention} has sent **{count}** messages in this server!")
    elif "avatar" in text or "pfp" in text or "profile pic" in text:
        await message.reply(f"🖼️ Avatar of {target_mention}:\n{target.display_avatar.url}")
    elif "joined" in text or "when did" in text:
        joined = target.joined_at.strftime("%d %B %Y") if target.joined_at else "Unknown"
        await message.reply(f"📅 {target_mention} joined this server on **{joined}**")
    elif "who is" in text:
        joined = target.joined_at.strftime("%d %B %Y") if target.joined_at else "Unknown"
        created = target.created_at.strftime("%d %B %Y") if target.created_at else "Unknown"
        roles = ", ".join([r.mention for r in target.roles[1:]]) if len(target.roles) > 1 else "No roles"
        await message.reply(
            f"**👤 Who is {target_mention}?**\n\n"
            f"**Joined Server:** {joined}\n"
            f"**Account Created:** {created}\n"
            f"**Roles:** {roles}\n"
            f"**ID:** `{target.id}`"
        )
    else:
        await message.reply(f"Yo, what's up {author.mention}? You called me? Tag me + `list` to see what I can do! Or use `/help`")
    return True

# --- ANTI-DOUBLE FIX - AT VERY END ---
_seen_ids = set()
_original_handle_tag_reply = handle_tag_reply

async def handle_tag_reply(bot, message):
    if message.id in _seen_ids:
        return True
    _seen_ids.add(message.id)
    if len(_seen_ids) > 2000:
        _seen_ids.clear()
        _seen_ids.add(message.id)
    return await _original_handle_tag_reply(bot, message)