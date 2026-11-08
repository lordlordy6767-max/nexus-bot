import pathlib
p = pathlib.Path('main.py')
t = p.read_text()

# Find masscreate block to insert delete before it
if '!massdelete' in t:
    print("ALREADY HAS DELETE")
else:
    # Find the line with masscreate
    marker = 'if message.content.startswith("!masscreate")'
    if marker not in t:
        marker = "if message.content.startswith('!masscreate')"
    if marker not in t:
        print("CANT FIND MASSCREATE - run: grep -n masscreate main.py")
    else:
        delete_code = '''    if message.content.startswith("!massdelete"):
        # !massdelete channels gaming  -> deletes all channels starting with gaming
        # !massdelete channels 5 gaming -> deletes gaming-1 to gaming-5
        try:
            parts = message.content.split()
            # parts = ['!massdelete', 'channels', 'gaming'] or ['!massdelete', 'channels', '5', 'gaming']
            if len(parts) < 3:
                await message.channel.send("Use: `!massdelete channels gaming` or `!massdelete channels 5 gaming`")
            elif parts[1] == "channels":
                deleted = 0
                if len(parts) == 4 and parts[2].isdigit():
                    count = int(parts[2])
                    prefix = parts[3]
                    for i in range(1, count+1):
                        name = f"{prefix}-{i}"
                        for ch in list(message.guild.channels):
                            if ch.name == name:
                                await ch.delete()
                                deleted += 1
                else:
                    prefix = parts[2]
                    for ch in list(message.guild.channels):
                        if ch.name.startswith(prefix):
                            await ch.delete()
                            deleted += 1
                await message.channel.send(f"🗑️ Deleted {deleted} channels starting with `{prefix}`")
            elif parts[1] == "roles":
                await message.channel.send("Role delete coming next - channels first!")
            else:
                await message.channel.send("Use: `!massdelete channels gaming`")
        except Exception as e:
            await message.channel.send(f"Delete failed: {e}")
        return

'''
        t = t.replace(marker, delete_code + marker, 1)
        p.write_text(t)
        print("DELETE ADDED!")
