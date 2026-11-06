import random

STORIES = {
    "spooky": [
        "👻 **The Last Message**\n\nMaya got a DM at 3AM from an account with no pfp. It just said 'don't look behind you.' She laughed... until her phone buzzed again. It was a photo of her own room. Taken from behind her chair.",
        "🌑 **The Empty VC**\n\nEvery night at 3:33 AM, one person joins the voice channel. No mic. No name you recognize. If you join to check, you hear your own breathing... but you're muted.",
        "🪞 **The Mirror Bot**\n\nSomeone added a bot that repeats everything you say, 10 seconds later. Funny at first. Until it started saying things BEFORE you said them.",
    ],
    "sweet": [
        "💛 **The Smallest Gift**\n\nLeo had 0 coins. But every day he reacted ❤️ to everyone's messages. On his birthday, the whole server pooled coins and gave him 10,000. He cried. He said it was the richest he'd ever felt.",
        "🌸 **The Long Distance Friend**\n\nAria and Noah never met IRL. They met in this server 2 years ago. Last week, Noah flew 3,000 miles just to say 'you were my best friend online, now be my best friend offline too.'",
        "🐶 **The Rescue**\n\nOne member was sad and quiet for a week. Nobody pushed. They just kept sending memes, good mornings, and 'we're here'. One day he came back and said 'you guys saved me without even knowing.'",
    ],
    "funny": [
        "😂 **The Admin Oops**\n\nThe admin tried to ban a spammer. He banned himself instead. For 10 minutes, the server had no admin, and the spammer became the most respected member in NEXUS history.",
        "🍕 **The Pizza War**\n\nTwo members argued for 3 hours about pineapple on pizza. It ended when someone ordered 20 pizzas, half with pineapple, half without. Everyone ate. Nobody won. Everyone was happy.",
        "🎮 **The Pro Gamer**\n\nJake said he was a pro gamer. He lost 12 games in a row. His excuse? 'My cat is sitting on my keyboard.' The cat was asleep on the bed in his camera.",
    ],
    "motivational": [
        "🔥 **The Comeback**\n\nKai failed 5 times. Got rejected. Got laughed at. On the 6th try, he built something everyone wanted. People asked 'what changed?' He said 'nothing. I just didn't quit on try 5.'",
        "🚀 **The First Step**\n\nEveryone in this server started at Level 0. Every legend here once sent their first 'hi'. Your story starts the same way. Just don't stop typing.",
    ],
}

def get_story(kind: str | None = None) -> tuple[str, str]:
    if kind and kind in STORIES:
        return kind, random.choice(STORIES[kind])
    kind = random.choice(list(STORIES.keys()))
    return kind, random.choice(STORIES[kind])