import pathlib
p = pathlib.Path('main.py')
lines = p.read_text().splitlines()

# Find start of massdelete block
start = None
end = None
for i,l in enumerate(lines):
    if '!massdelete' in l and 'startswith' in l:
        start = i
        base = l[:len(l)-len(l.lstrip())]  # 8 spaces
        print(f"Start {i+1} base={len(base)}")
    if start is not None and i > start:
        if '!masscreate' in l and 'startswith' in l:
            end = i
            print(f"End {i+1} = masscreate")
            break

if start is None or end is None:
    print("NOT FOUND")
else:
    B = base
    I = B + "    "  # 1 level in
    J = B + "        "  # 2 levels
    K = B + "            "  # 3 levels
    L = B + "                "  # 4 levels
    new = [
        B + 'if message.content.startswith("!massdelete"):',
        I + '# !massdelete channels gaming',
        I + 'try:',
        J + 'parts = message.content.split()',
        J + 'if len(parts) < 3:',
        K + 'await message.channel.send("Use: `!massdelete channels gaming` or `!massdelete channels 5 gaming`")',
        J + 'elif parts[1] == "channels":',
        K + 'deleted = 0',
        K + 'if len(parts) == 4 and parts[2].isdigit():',
        L + 'count = int(parts[2])',
        L + 'prefix = parts[3]',
        L + 'for i in range(1, count+1):',
        L + '    name = f"{prefix}-{i}"',
        L + '    for ch in list(message.guild.channels):',
        L + '        if ch.name == name:',
        L + '            await ch.delete()',
        L + '            deleted += 1',
        K + 'else:',
        L + 'prefix = parts[2]',
        L + 'for ch in list(message.guild.channels):',
        L + '    if ch.name.startswith(prefix):',
        L + '        await ch.delete()',
        L + '        deleted += 1',
        K + 'await message.channel.send(f"Deleted {deleted} channels starting with {prefix}")',
        J + 'elif parts[1] == "roles":',
        K + 'await message.channel.send("Role delete coming next!")',
        J + 'else:',
        K + 'await message.channel.send("Use: `!massdelete channels gaming`")',
        I + 'except Exception as e:',
        J + 'await message.channel.send(f"Delete failed: {e}")',
        I + 'return',
        '',
    ]
    lines[start:end] = new
    p.write_text("\n".join(lines) + "\n")
    print("FIXED!")
