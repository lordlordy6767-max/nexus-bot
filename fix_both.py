import pathlib
p = pathlib.Path('main.py')
lines = p.read_text().splitlines()

# Find massdelete start to aiimage start - replace everything in between
start = next(i for i,l in enumerate(lines) if '!massdelete' in l and 'startswith' in l)
end = next(i for i,l in enumerate(lines) if '!aiimage' in l and 'startswith' in l)
print(f"replacing {start+1} to {end+1}")

B="    "
I="        "
J="            "
K="                "
L="                    "
M="                        "

new = [
B+'if message.content.startswith("!massdelete"):',
I+'try:',
J+'parts = message.content.split()',
J+'if len(parts) >= 3 and parts[1] == "channels":',
K+'prefix = parts[2]',
K+'deleted = 0',
K+'for ch in list(message.guild.channels):',
L+'if ch.name.startswith(prefix):',
M+'await ch.delete()',
M+'deleted += 1',
K+'await message.channel.send(f"Deleted {deleted} channels starting with {prefix}")',
K+'return',
J+'await message.channel.send("Which channels should I delete? Reply with names separated by comma.\\nExample: `gaming, music, chat`\\nOr reply `all text` / `all voice` / `cancel`")',
J+'def check(m):',
K+'return m.author == message.author and m.channel == message.channel',
J+'try:',
K+'reply = await client.wait_for("message", check=check, timeout=60.0)',
J+'except:',
K+'await message.channel.send("Timed out - no channels deleted.")',
K+'return',
J+'text = reply.content.strip().lower()',
J+'if text == "cancel":',
K+'await message.channel.send("Cancelled - nothing deleted.")',
K+'return',
J+'deleted = 0',
J+'notfound = []',
J+'if text == "all text":',
K+'for ch in list(message.guild.text_channels):',
L+'if ch != message.channel:',
M+'await ch.delete()',
M+'deleted += 1',
J+'elif text == "all voice":',
K+'for ch in list(message.guild.voice_channels):',
L+'await ch.delete()',
L+'deleted += 1',
J+'else:',
K+'names = [n.strip().lower() for n in reply.content.split(",")]',
K+'for name in names:',
L+'found = False',
L+'for ch in list(message.guild.channels):',
M+'if ch.name.lower() == name:',
M+'    await ch.delete()',
M+'    deleted += 1',
M+'    found = True',
L+'if not found:',
M+'notfound.append(name)',
J+'msg = f"Deleted {deleted} channels."',
J+'if notfound:',
K+'msg += " Not found: " + ", ".join(notfound)',
J+'await message.channel.send(msg)',
I+'except Exception as e:',
J+'await message.channel.send(f"Delete failed: {e}")',
I+'return',
'',
B+'if message.content.startswith("!masscreate"):',
I+'blocked = check_paywall(message.author.id)',
I+'if blocked:',
J+'await message.reply(blocked); return',
I+'try:',
J+'parts = message.content.split()',
J+'# !masscreate channels 5 gaming',
J+'kind = parts[1]; count = parts[2]; base = parts[3]',
J+'await message.reply(await premium_all.mass_create(message, kind, count, base))',
I+'except:',
J+'await message.reply("Use: `!masscreate channels 5 gaming`")',
J+'return',
'',
]
lines[start:end] = new
p.write_text("\n".join(lines)+"\n")
print("FIXED BOTH!")
