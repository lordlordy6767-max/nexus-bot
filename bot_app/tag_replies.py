import discord

async def handle_tag_reply(bot, message: discord.Message) -> bool:
    # Return True if we replied, False if not
    if message.author.bot:
        return False
    if bot.user is None:
        return False
    if bot.user not in message.mentions:
        return False

    text = message.content.lower()

    if "who is the king" in text:
        await message.reply("KING Tyler Hayes, obviously 👑 No debate!")
    elif "help" in text:
        await message.reply(f"Need help {message.author.mention}? Use `/help` to see all commands!")
    elif "ping" in text:
        await message.reply("Pong! 🏓")
    elif any(w in text for w in ["hello", "hi", "hey", "yo"]):
        await message.reply(f"Hello {message.author.mention}! Welcome to the future. 🔥")
    else:
        await message.reply(f"Yo, what's up {message.author.mention}? You called me? Use `/help`")

    return True