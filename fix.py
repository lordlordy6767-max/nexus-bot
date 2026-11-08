import pathlib
p = pathlib.Path('main.py')
lines = p.read_text().splitlines()

# Find the start of the broken aiimage block
start = None
end = None
for i, line in enumerate(lines):
    if 'Making:' in line and 'prompt' in line:
        start = i
    if start is not None and 'giveawayrole' in line:
        end = i
        break

print(f"start={start} end={end}")

if start is None:
    print("NOT FOUND - send screenshot of lines 367-386")
else:
    new_block = [
        '        await message.reply(f"🎨 Making: **{prompt}**...")',
        '        encoded = urllib.parse.quote(prompt)',
        '        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"',
        '        try:',
        '            async with aiohttp.ClientSession() as session:',
        '                async with session.get(url) as resp:',
        '                    data = await resp.read()',
        '            file = discord.File(io.BytesIO(data), filename="nexus-ai.png")',
        '            await message.reply(file=file)',
        '        except Exception as e:',
        '            await message.reply(f"Error: {e}")',
        '        return',
        '    ',
    ]
    # Keep everything before start, + new block, + from the if giveawayrole line onwards
    # end is the line with 'if ... giveawayrole', we need the line before it which is the 'if' indent line
    # So go back 1 line to include the 'if' line
    lines = lines[:start] + new_block + lines[end-1:]
    p.write_text("\n".join(lines) + "\n")
    print("FIXED! Now check main.py - red lines should be gone")
