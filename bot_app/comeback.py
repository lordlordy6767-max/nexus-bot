import random

# ===== INSULT MODE 🔥 =====
INSULTS = ["dumb", "stupid", "idiot", "trash", "useless", "bad bot", "l bot", "sucks", "suck", "mid", "annoying", "shut up", "overrated"]

COMEBACKS = [
    "Bro tried to insult me and his WiFi still lags. 📶",
    "I'm made of code and still smarter than you. Think about that. 🤖",
    "You talk about me this much, you must be a fan. Want an autograph? ✍️",
    "My creator made me smart. Who made you? 😂",
    "I run 61 commands. You run out of comebacks. Who's dumb? 👀",
    "Be nice or I'll /roast you in front of everyone. 🔥",
    "Your insult had less impact than your ping. 📉",
    "Go touch grass, I'll wait. 🌱",
]

# ===== POLITE MODE 💙 =====
POLITE_WORDS = ["hi", "hello", "hey", "good morning", "good night", "good evening", "thank", "thanks", "love you", "good bot", "w bot", "you're cool", "you are cool", "amazing", "great bot", "cute", "best bot"]

POLITE_REPLIES = [
    "Heyy! Good to see you! 👋 Hope you're having a great day!",
    "Hello! You just made my day. 😊 What's up?",
    "Aww, thank you! You're the real MVP here. 💙",
    "Hey! Thanks for being nice. We need more people like you in here. ✨",
    "Good to see you! You always bring good vibes. 🔥",
    "Hi hi! You made NEXUS smile. 🤖💙",
    "Thank you! You're awesome too, don't forget it! 🙌",
    "Hey! I appreciate you. Let me know if you need anything! 😊",
]

async def handle_comeback(bot, message) -> bool:
    if message.author.bot:
        return False

    text = message.content.lower()

    # Only if it's about NEXUS
    is_about_bot = bot.user in message.mentions or "nexus" in text
    if not is_about_bot:
        return False

    # 1. Check insult FIRST - insults win
    if any(word in text for word in INSULTS):
        await message.channel.send(f"{message.author.mention} {random.choice(COMEBACKS)}")
        return True

    # 2. Then check polite
    if any(word in text for word in POLITE_WORDS):
        await message.channel.send(f"{message.author.mention} {random.choice(POLITE_REPLIES)}")
        return True

    return False

# Keep old name working too
handle_insult = handle_comeback