import discord
import random

async def handle_tag_reply(bot, message: discord.Message) -> bool:
    # Return True if we replied, False if not
    if message.author.bot:
        return False
    if bot.user is None:
        return False
    if bot.user not in message.mentions:
        return False

    text = message.content.lower()
    author = message.author

    # Get target = first mentioned user who is NOT the bot
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
            "`cook @user` • `roast @user` • `rate @user` • `expose @user` • `cancel @user`\n\n"
            "**❤️ LOVE:**\n"
            "`love you` • `hug @user` • `kiss @user` • `ship @user @user` • `marry @user` • `marry me`\n\n"
            "**🥊 FIGHT:**\n"
            "`fight @user` • `slap @user` • `vs @user` • `jumpscare @user` • `bonk @user` • `bite @user` • `lick @user` • `kill @user` • `arrest @user` • `jail @user`\n\n"
            "**✨ AURA / RIZZ:**\n"
            "`aura @user` • `rizz @user` • `vibe check @user` • `how gay is @user` • `how smart is @user` • `how rich is @user` • `iq @user` • `dumbest @user` • `smartest @user` • `pat @user`\n\n"
            "**🔮 PREDICT:**\n"
            "`predict @user` • `fortune @user` • `when will @user get married`\n\n"
            "**🎲 GAME / LUCK:**\n"
            "`coinflip` • `dice` • `8ball`\n\n"
            "**🎤 MUSIC / FUN:**\n"
            "`sing` • `sing for @user` • `rap @user`\n\n"
            "**🤖 BOT:**\n"
            "`are you real` • `are you smart` • `ping` • `hello`\n\n"
            "Or use `/help` for ALL commands!"
        )
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
    else:
        await message.reply(f"Yo, what's up {author.mention}? You called me? Tag me + `list` to see what I can do! Or use `/help`")

    return True