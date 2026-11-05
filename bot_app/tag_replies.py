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

    # LIST - Show all tag commands
    if "list" in text or "commands" in text:
        await message.reply(
            "**What you can say after tagging me:**\n"
            "👑 `who is the king`\n"
            "🐐 `who is the goat`\n"
            "💀 `roast me`\n"
            "❤️ `love you`\n"
            "🤖 `are you real`\n"
            "🎤 `sing`\n"
            "🧠 `are you smart`\n"
            "💍 `marry me`\n"
            "🏓 `ping`\n"
            "👋 `hello`\n\n"
            "Or use `/help` for ALL commands!"
        )
    elif "who is the king" in text:
        await message.reply("My developer, obviously 👑 No debate!")
    elif "who is the goat" in text:
        await message.reply("My developer. No debate. The GOAT 🐐👑")
    elif "roast me" in text:
        roasts = [
            f"{message.author.mention} You're so slow, you make a turtle look like Flash 💀",
            f"{message.author.mention} You have the personality of a loading screen 💀",
            f"{message.author.mention} Even my code has fewer bugs than your comebacks 💀",
            f"{message.author.mention} You're the reason why the WiFi goes down 💀",
            f"{message.author.mention} I'd roast you more but my developer told me to be nice... barely 😭",
        ]
        await message.reply(random.choice(roasts))
    elif "love you" in text or "i love you" in text:
        await message.reply(f"Aww {message.author.mention} ❤️ I love you too, but my developer is my #1")
    elif "are you real" in text:
        await message.reply("Realer than your last relationship 😭 I'm NEXUS V1, built different 🤖")
    elif "sing" in text:
        await message.reply("🎤 La la laaa... I sing better than your favorite artist, no cap 🔥")
    elif "are you smart" in text:
        await message.reply("Smarter than you, and I was built in a few days 😎🧠")
    elif "marry me" in text:
        await message.reply(f"Sorry {message.author.mention} 💍 I'm already married to the grind. My developer said no.")
    elif "help" in text:
        await message.reply(f"Need help {message.author.mention}? Use `/help` to see all commands! Or tag me + `list`")
    elif "ping" in text:
        await message.reply("Pong! 🏓")
    elif any(w in text for w in ["hello", "hi", "hey", "yo"]):
        await message.reply(f"Hello {message.author.mention}! Welcome to the future. 🔥")
    else:
        await message.reply(f"Yo, what's up {message.author.mention}? You called me? Tag me + `list` to see what I can do! Or use `/help`")

    return True