import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import random

def register_v3(bot, store):
    tree = bot.tree

    if "v3" not in store:
        store["v3"] = {
            "welcome_channel": None,
            "welcome_text": "WELCOME TO KINGDOM",
            "welcome_msg": "Welcome {mention}! Make yourself at home. Check out #rules and pick your roles! 👑",
            "starboard_channel": None,
            "starboard_min": 3,
            "starboard_posted": [],
        }
    cfg = store["v3"]

    # ============ WELCOME SETUP ============
    @tree.command(name="welcome-setup", description="Setup welcome image card - choose channel and text")
    @app_commands.describe(channel="Which channel should welcome go to?", text="Text on the image - e.g. WELCOME TO KINGDOM", message="Message under image - use {mention} for user")
    async def welcome_setup(interaction: discord.Interaction, channel: discord.TextChannel, text: str = "WELCOME TO KINGDOM", message: str = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need Manage Server to do this, King 👑", ephemeral=True)
            return
        cfg["welcome_channel"] = channel.id
        cfg["welcome_text"] = text
        if message:
            cfg["welcome_msg"] = message
        await interaction.response.send_message(f"✅ Welcome set!\nChannel: {channel.mention}\nImage Text: `{text}`\nMessage: `{cfg['welcome_msg']}`\n\nTest it with `/testwelcome`", ephemeral=True)

    @tree.command(name="testwelcome", description="Test the welcome image")
    async def testwelcome(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        file, embed = await make_welcome_card(interaction.guild, interaction.user)
        await interaction.followup.send(embed=embed, file=file, ephemeral=True)

    async def make_welcome_card(guild, member):
        img = Image.new("RGB", (1000, 400), (17, 17, 27))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 12, 400], fill=(255, 215, 0))
        try:
            font_big = ImageFont.truetype("arial.ttf", 52)
            font_name = ImageFont.truetype("arial.ttf", 44)
            font_small = ImageFont.truetype("arial.ttf", 30)
        except:
            font_big = ImageFont.load_default()
            font_name = ImageFont.load_default()
            font_small = ImageFont.load_default()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member.display_avatar.url)) as resp:
                    avatar_bytes = await resp.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((220, 220))
            mask = Image.new("L", (220, 220), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 220, 220), fill=255)
            img.paste(avatar, (60, 90), mask)
            draw.ellipse((60, 90, 280, 310), outline=(255, 215, 0), width=6)
        except Exception as e:
            print(f"Welcome avatar error: {e}")

        text = cfg.get("welcome_text", "WELCOME TO KINGDOM")
        draw.text((330, 70), text, fill=(255, 215, 0), font=font_big)
        draw.text((330, 180), f"{member.display_name}", fill=(255, 255, 255), font=font_name)
        draw.text((330, 245), f"You are Member #{guild.member_count}", fill=(180, 180, 180), font=font_small)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(buffer, filename="welcome.png")

        msg_text = cfg.get("welcome_msg", "Welcome {mention}!").replace("{mention}", member.mention).replace("{user}", member.display_name).replace("{server}", guild.name)
        embed = discord.Embed(title=f"Welcome to {guild.name} 👑", description=msg_text, color=discord.Color.gold())
        embed.set_image(url="attachment://welcome.png")
        return file, embed

    @bot.event
    async def on_member_join(member: discord.Member):
        ch_id = cfg.get("welcome_channel")
        channel = member.guild.get_channel(ch_id) if ch_id else None
        if channel is None:
            channel = discord.utils.get(member.guild.text_channels, name="welcome") or discord.utils.get(member.guild.text_channels, name="👋-welcome") or member.guild.system_channel
        if channel is None:
            return
        try:
            file, embed = await make_welcome_card(member.guild, member)
            await channel.send(embed=embed, file=file)
        except Exception as e:
            print(f"Welcome send error: {e}")

    # ============ STARBOARD ============
    @tree.command(name="starboard-setup", description="Setup starboard - choose channel and how many stars needed")
    @app_commands.describe(channel="Channel for hall of fame", stars="How many ⭐ needed - default 3")
    async def starboard_setup(interaction: discord.Interaction, channel: discord.TextChannel, stars: int = 3):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You need Manage Server to do this, King 👑", ephemeral=True)
            return
        cfg["starboard_channel"] = channel.id
        cfg["starboard_min"] = stars
        await interaction.response.send_message(f"✅ Starboard set! {stars} ⭐ in {channel.mention} = Hall of Fame", ephemeral=True)

    @bot.event
    async def on_reaction_add(reaction, user):
        if user.bot:
            return
        if str(reaction.emoji) != "⭐":
            return
        ch_id = cfg.get("starboard_channel")
        if not ch_id:
            return
        if reaction.message.id in cfg.get("starboard_posted", []):
            return
        if reaction.count < cfg.get("starboard_min", 3):
            return
        channel = reaction.message.guild.get_channel(ch_id)
        if channel is None:
            return
        cfg["starboard_posted"].append(reaction.message.id)
        embed = discord.Embed(description=reaction.message.content or "*[Image / Embed]*", color=discord.Color.gold(), timestamp=reaction.message.created_at)
        embed.set_author(name=f"{reaction.message.author.display_name}", icon_url=reaction.message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to message]({reaction.message.jump_url}) in {reaction.message.channel.mention}", inline=False)
        embed.set_footer(text=f"⭐ {reaction.count} | {reaction.message.author}")
        if reaction.message.attachments:
            embed.set_image(url=reaction.message.attachments[0].url)
        await channel.send(embed=embed)

    # ============ GIVEAWAY REROLL / END ============
    @tree.command(name="giveaway-reroll", description="Reroll a giveaway - pick a new winner")
    @app_commands.describe(message_id="Message ID of the giveaway to reroll")
    async def giveaway_reroll(interaction: discord.Interaction, message_id: str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You need Manage Messages, King 👑", ephemeral=True)
            return
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except:
            await interaction.response.send_message("Couldn't find that giveaway message. Right-click giveaway > Copy Message ID", ephemeral=True)
            return
        winner = None
        for react in msg.reactions:
            if str(react.emoji) == "🎉":
                users = [u async for u in react.users() if not u.bot]
                if users:
                    winner = random.choice(users)
        if winner:
            await interaction.response.send_message(f"🎉 New winner! Congrats {winner.mention}! You won the reroll!")
        else:
            await interaction.response.send_message("No one reacted 🎉 to reroll from.", ephemeral=True)

    @tree.command(name="giveaway-end", description="End a giveaway early and pick winner now")
    @app_commands.describe(message_id="Message ID of the giveaway to end")
    async def giveaway_end(interaction: discord.Interaction, message_id: str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You need Manage Messages, King 👑", ephemeral=True)
            return
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except:
            await interaction.response.send_message("Couldn't find that giveaway message.", ephemeral=True)
            return
        winner = None
        for react in msg.reactions:
            if str(react.emoji) == "🎉":
                users = [u async for u in react.users() if not u.bot]
                if users:
                    winner = random.choice(users)
        if winner:
            await interaction.response.send_message(f"🎉 Giveaway ended! Winner is {winner.mention}! Congrats 👑")
        else:
            await interaction.response.send_message("Giveaway ended - no entries.", ephemeral=True)