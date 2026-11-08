import pathlib
p = pathlib.Path('main.py')
lines = p.read_text().splitlines()
# Find the prompt line
for i, l in enumerate(lines):
    if 'prompt = message.content.replace("!aiimage"' in l:
        indent = l[:len(l)-len(l.lstrip())]
        print(f"Found at line {i+1} indent={len(indent)}")
        # Replace next 5 lines with correct block
        new_block = [
            indent + 'style_suffix = ""',
            indent + 'if prompt.lower().startswith("anime "):',
            indent + '    prompt = prompt[6:].strip()',
            indent + '    style_suffix = ", anime style, vibrant, detailed anime art"',
            indent + 'prompt = prompt + style_suffix',
        ]
        # Delete old 5 lines after prompt line (if they are our bad block)
        # Check: next line contains style_suffix
        if 'style_suffix' in lines[i+1]:
            lines[i+1:i+6] = new_block
            p.write_text("\n".join(lines) + "\n")
            print("INDENT FIXED!")
        else:
            print("Next line is:", lines[i+1])
        break
