import discord
from discord import app_commands
import random
from bot_app.wallet import get_bal, add

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