import pathlib
p = pathlib.Path('main.py')
t = p.read_text()

# Find our block and replace with retry version
old_start = '        await message.reply(f"🎨 Making: **{prompt}**...")'
idx = t.find(old_start)
if idx == -1:
    print("NOT FOUND")
else:
    # Find the 'return' after it
    end_idx = t.find("\n        return", idx) + len("\n        return")
    new_block = '''        await message.reply(f"🎨 Making: **{prompt}**...")
        import random
        encoded = urllib.parse.quote(prompt)
        data = None
        for attempt in range(3):
            seed = random.randint(1, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.read()
                        # Check if it's really an image (PNG starts with this)
                        if len(data) > 10000:
                            break
                        print(f"Retry {attempt} got {len(data)} bytes")
            except Exception as e:
                print(f"Retry {attempt} error: {e}")
                continue
        if not data or len(data) < 10000:
            await message.reply("Pollinations is busy right now, try again in 10 seconds!")
        else:
            file = discord.File(io.BytesIO(data), filename="nexus-ai.png")
            await message.reply(file=file)
        return'''
    t = t[:idx] + new_block + t[end_idx:]
    p.write_text(t)
    print("FIXED RETRY!")
