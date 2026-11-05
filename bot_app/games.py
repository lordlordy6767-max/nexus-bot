import discord
from discord import app_commands
import random
import aiohttp
from bot_app.wallet import get_bal, add
try:
    from bot_app.wallet import _balances
except Exception:
    _balances = {}

def register_games_commands(bot, store):

    @bot.tree.command(name="coinflip", description="Flip a coin - bet coins!")
    @app_commands.describe(choice="heads or tails", bet="How many coins to bet")
    async def coinflip(interaction: discord.Interaction, choice: str, bet: int):
        choice = choice.lower()
        if choice not in ["heads", "tails"]:
            await interaction.response.send_message("Pick `heads` or `tails` King 👑", ephemeral=True)
            return
        if bet <= 0:
            await interaction.response.send_message("Bet must be more than 0!", ephemeral=True)
            return
        bal = get_bal(interaction.user.id)
        if bet > bal:
            await interaction.response.send_message(f"You only have {bal} coins! 💰 Do /daily first!", ephemeral=True)
            return
        result = random.choice(["heads", "tails"])
        emoji = "🪙" if result == "heads" else "👑"
        if result == choice:
            new_bal = add(interaction.user.id, bet)
            embed = discord.Embed(title="🎉 YOU WON!", color=discord.Color.green())
            embed.add_field(name="Result", value=f"{emoji} {result.upper()}", inline=False)
            embed.add_field(name="Won", value=f"+{bet} coins", inline=True)
            embed.add_field(name="New Balance", value=f"{new_bal} coins", inline=True)
        else:
            new_bal = add(interaction.user.id, -bet)
            embed = discord.Embed(title="💔 YOU LOST!", color=discord.Color.red())
            embed.add_field(name="Result", value=f"{emoji} {result.upper()}", inline=False)
            embed.add_field(name="Lost", value=f"-{bet} coins", inline=True)
            embed.add_field(name="New Balance", value=f"{new_bal} coins", inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="dice", description="Roll a dice 1-6")
    async def dice(interaction: discord.Interaction):
        roll = random.randint(1, 6)
        dice_emojis = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        embed = discord.Embed(title="🎲 DICE ROLL", color=discord.Color.gold())
        embed.add_field(name=f"{interaction.user.display_name} rolled", value=f"{dice_emojis[roll]} **{roll}**", inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="rps", description="Rock Paper Scissors vs someone!")
    @app_commands.describe(opponent="Who do you want to challenge?", choice="rock, paper or scissors")
    async def rps(interaction: discord.Interaction, opponent: discord.Member, choice: str):
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            await interaction.response.send_message("Pick `rock`, `paper` or `scissors`!", ephemeral=True)
            return
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("You can't play against yourself 😂", ephemeral=True)
            return
        bot_choice = random.choice(["rock", "paper", "scissors"])
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        if choice == bot_choice:
            result = "It's a DRAW! 🤝"
        elif (choice == "rock" and bot_choice == "scissors") or (choice == "paper" and bot_choice == "rock") or (choice == "scissors" and bot_choice == "paper"):
            result = f"🎉 {interaction.user.display_name} WINS!"
        else:
            result = f"🎉 {opponent.display_name} WINS!"
        embed = discord.Embed(title="✂️ ROCK PAPER SCISSORS", color=discord.Color.blue())
        embed.add_field(name=interaction.user.display_name, value=f"{emojis[choice]} {choice}", inline=True)
        embed.add_field(name=opponent.display_name, value=f"{emojis[bot_choice]} {bot_choice}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="slots", description="Slot machine - bet coins!")
    @app_commands.describe(bet="How many coins to bet")
    async def slots(interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message("Bet must be more than 0!", ephemeral=True)
            return
        bal = get_bal(interaction.user.id)
        if bet > bal:
            await interaction.response.send_message(f"You only have {bal} coins! 💰 Do /daily first!", ephemeral=True)
            return
        symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣", "⭐", "🔔"]
        r1, r2, r3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        embed = discord.Embed(title="🎰 SLOTS", color=discord.Color.purple())
        embed.add_field(name="Spin", value=f"| {r1} | {r2} | {r3} |", inline=False)
        if r1 == r2 == r3:
            win = bet * 5
            new_bal = add(interaction.user.id, win)
            embed.add_field(name="JACKPOT! 🎉", value=f"+{win} coins! New Balance: {new_bal}", inline=False)
            embed.color = discord.Color.gold()
        elif r1 == r2 or r2 == r3 or r1 == r3:
            win = bet * 2
            new_bal = add(interaction.user.id, win)
            embed.add_field(name="Nice! You got 2 matching!", value=f"+{win} coins! New Balance: {new_bal}", inline=False)
        else:
            new_bal = add(interaction.user.id, -bet)
            embed.add_field(name="No match 😢", value=f"-{bet} coins! New Balance: {new_bal}", inline=False)
        await interaction.response.send_message(embed=embed)

    QUESTIONS = [
        ("What is the capital of France?", ["London", "Paris", "Berlin", "Madrid"], 1),
        ("What is 5 + 7?", ["10", "11", "12", "13"], 2),
        ("Which planet is called the Red Planet?", ["Venus", "Jupiter", "Mars", "Saturn"], 2),
        ("Who wrote Harry Potter?", ["J.K. Rowling", "Tolkien", "Shakespeare", "King"], 0),
        ("What is the largest ocean?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3),
    ]

    @bot.tree.command(name="trivia", description="Answer a trivia question - win 100 coins!")
    async def trivia(interaction: discord.Interaction):
        q, options, correct = random.choice(QUESTIONS)
        class TriviaButton(discord.ui.Button):
            def __init__(self, label, index):
                super().__init__(label=label, style=discord.ButtonStyle.primary)
                self.index = index
            async def callback(self, btn_interaction: discord.Interaction):
                if btn_interaction.user.id != interaction.user.id:
                    await btn_interaction.response.send_message("Not your question!", ephemeral=True)
                    return
                for child in self.view.children:
                    child.disabled = True
                if self.index == correct:
                    new_bal = add(interaction.user.id, 100)
                    await btn_interaction.response.send_message(f"✅ CORRECT! +100 coins! New Balance: {new_bal} 🎉")
                else:
                    await btn_interaction.response.send_message(f"❌ WRONG! Correct was: **{options[correct]}**")
                try:
                    await btn_interaction.message.edit(view=self.view)
                except Exception:
                    pass
        view = discord.ui.View(timeout=30)
        for i, opt in enumerate(options):
            view.add_item(TriviaButton(label=opt, index=i))
        embed = discord.Embed(title="🧠 TRIVIA", description=q, color=discord.Color.teal())
        embed.set_footer(text="Win 100 coins if correct!")
        await interaction.response.send_message(embed=embed, view=view)

    @bot.tree.command(name="memes", description="Get a random meme 😂")
    async def memes(interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://meme-api.com/gimme") as r:
                    data = await r.json()
            embed = discord.Embed(title=data.get("title", "MEME 😂"), color=discord.Color.blurple())
            embed.set_image(url=data.get("url"))
            embed.set_footer(text=f"From r/{data.get('subreddit', 'memes')} | 👍 {data.get('ups', 0)}")
            await interaction.followup.send(embed=embed)
        except Exception:
            await interaction.followup.send("Meme API is down right now 😢 Try again in a sec!")

    # ===== MY IDEAS =====

    SHOP_ITEMS = {
        "mysterybox": {"name": "🎁 Mystery Box", "price": 500, "desc": "Random reward 100-1000 coins!"},
        "vip": {"name": "👑 VIP Role", "price": 5000, "desc": "Get VIP role in server"},
        "color": {"name": "🎨 Color Role", "price": 2000, "desc": "Get a cool color role"},
        "boost": {"name": "🚀 Daily Boost", "price": 1000, "desc": "Bragging rights - you are boosted!"},
    }

    @bot.tree.command(name="shop", description="See the shop 🛒")
    async def shop(interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 NEXUS SHOP", color=discord.Color.gold())
        bal = get_bal(interaction.user.id)
        embed.add_field(name="Your Balance", value=f"{bal} coins 💰", inline=False)
        for key, item in SHOP_ITEMS.items():
            embed.add_field(name=f"{item['name']} - {item['price']} coins", value=f"`/buy {key}` - {item['desc']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="buy", description="Buy something from the shop")
    @app_commands.describe(item="mysterybox, vip, color, boost")
    async def buy(interaction: discord.Interaction, item: str):
        item = item.lower()
        if item not in SHOP_ITEMS:
            await interaction.response.send_message("That item doesn't exist! Do `/shop` to see items.", ephemeral=True)
            return
        data = SHOP_ITEMS[item]
        bal = get_bal(interaction.user.id)
        if bal < data["price"]:
            await interaction.response.send_message(f"You need {data['price']} coins! You have {bal} 💰", ephemeral=True)
            return
        if item == "mysterybox":
            reward = random.randint(100, 1000)
            new_bal = add(interaction.user.id, -data["price"] + reward)
            await interaction.response.send_message(f"🎁 You opened Mystery Box and got **{reward} coins**! New Balance: {new_bal}")
            return
        if item in ["vip", "color"]:
            role_name = "VIP" if item == "vip" else "Color"
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                try:
                    await interaction.user.add_roles(role)
                except Exception:
                    pass
            new_bal = add(interaction.user.id, -data["price"])
            await interaction.response.send_message(f"✅ You bought {data['name']}! New Balance: {new_bal} 🎉")
            return
        new_bal = add(interaction.user.id, -data["price"])
        await interaction.response.send_message(f"✅ You bought {data['name']}! New Balance: {new_bal} 🚀")

    @bot.tree.command(name="topmoney", description="Top 10 richest in NEXUS 💰")
    async def topmoney(interaction: discord.Interaction):
        if not _balances:
            await interaction.response.send_message("No one has coins yet! Do /daily first 💰")
            return
        sorted_bal = sorted(_balances.items(), key=lambda x: x[1], reverse=True)[:10]
        embed = discord.Embed(title="🏆 RICHEST IN NEXUS", color=discord.Color.gold())
        lines = []
        for i, (uid, bal) in enumerate(sorted_bal, 1):
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            lines.append(f"{medal} **{name}** - {bal} coins")
        embed.description = "\n".join(lines)
        my_bal = get_bal(interaction.user.id)
        all_sorted = sorted(_balances.items(), key=lambda x: x[1], reverse=True)
        my_rank = next((i+1 for i, (uid, _) in enumerate(all_sorted) if str(uid) == str(interaction.user.id)), 0)
        embed.set_footer(text=f"You are #{my_rank} with {my_bal} coins")
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="blackjack", description="Play Blackjack vs dealer 🃏")
    @app_commands.describe(bet="How many coins to bet")
    async def blackjack(interaction: discord.Interaction, bet: int):
        if bet <= 0:
            await interaction.response.send_message("Bet must be more than 0!", ephemeral=True)
            return
        bal = get_bal(interaction.user.id)
        if bet > bal:
            await interaction.response.send_message(f"You only have {bal} coins! 💰 Do /daily first!", ephemeral=True)
            return

        def draw():
            return random.choice([2,3,4,5,6,7,8,9,10,10,10,10,11])
        def total(hand):
            s = sum(hand)
            aces = hand.count(11)
            while s > 21 and aces:
                s -= 10
                aces -= 1
            return s

        player = [draw(), draw()]
        dealer = [draw(), draw()]

        class BJView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.done = False
            def make_embed(self, reveal=False):
                p = total(player)
                d = total(dealer) if reveal else dealer[0]
                e = discord.Embed(title="🃏 BLACKJACK", color=discord.Color.green())
                e.add_field(name="Your Hand", value=f"{player} = **{p}**", inline=False)
                if reveal:
                    e.add_field(name="Dealer Hand", value=f"{dealer} = **{d}**", inline=False)
                else:
                    e.add_field(name="Dealer Hand", value=f"[{dealer[0]}, ?] = **{d}+**", inline=False)
                e.add_field(name="Bet", value=f"{bet} coins", inline=True)
                return e
            @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🃏")
            async def hit(self, btn_inter: discord.Interaction, button: discord.ui.Button):
                if btn_inter.user.id != interaction.user.id:
                    await btn_inter.response.send_message("Not your game!", ephemeral=True)
                    return
                player.append(draw())
                if total(player) > 21:
                    new_bal = add(interaction.user.id, -bet)
                    e = self.make_embed(reveal=True)
                    e.add_field(name="💔 BUST! You lost", value=f"-{bet} coins! New Balance: {new_bal}", inline=False)
                    for c in self.children: c.disabled = True
                    await btn_inter.response.edit_message(embed=e, view=self)
                elif total(player) == 21:
                    await self.stand_callback(btn_inter)
                else:
                    await btn_inter.response.edit_message(embed=self.make_embed(), view=self)
            @discord.ui.button(label="Stand", style=discord.ButtonStyle.success, emoji="✋")
            async def stand(self, btn_inter: discord.Interaction, button: discord.ui.Button):
                await self.stand_callback(btn_inter)
            async def stand_callback(self, btn_inter):
                if btn_inter.user.id != interaction.user.id:
                    await btn_inter.response.send_message("Not your game!", ephemeral=True)
                    return
                while total(dealer) < 17:
                    dealer.append(draw())
                p, d = total(player), total(dealer)
                e = self.make_embed(reveal=True)
                for c in self.children: c.disabled = True
                if d > 21 or p > d:
                    win = int(bet * 2.5) if p == 21 and len(player) == 2 else bet * 2
                    # win is total return, profit = win - bet, but we already didn't deduct, so add profit
                    profit = win - bet if p == 21 and len(player) == 2 else bet
                    # Simpler: if win, add bet as profit, blackjack extra
                    if p == 21 and len(player) == 2:
                        profit = int(bet * 1.5)
                    else:
                        profit = bet
                    new_bal = add(interaction.user.id, profit)
                    e.add_field(name="🎉 YOU WIN!", value=f"+{profit} coins! New Balance: {new_bal}", inline=False)
                elif p == d:
                    e.add_field(name="🤝 PUSH - Draw!", value=f"Bet returned. Balance: {get_bal(interaction.user.id)}", inline=False)
                else:
                    new_bal = add(interaction.user.id, -bet)
                    e.add_field(name="💔 Dealer Wins!", value=f"-{bet} coins! New Balance: {new_bal}", inline=False)
                await btn_inter.response.edit_message(embed=e, view=self)

        view = BJView()
        # Instant blackjack check
        if total(player) == 21:
            profit = int(bet * 1.5)
            new_bal = add(interaction.user.id, profit)
            e = view.make_embed(reveal=True)
            e.add_field(name="🎉 BLACKJACK!", value=f"+{profit} coins! New Balance: {new_bal}", inline=False)
            await interaction.response.send_message(embed=e)
            return
        await interaction.response.send_message(embed=view.make_embed(), view=view)