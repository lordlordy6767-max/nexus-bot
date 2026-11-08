import pathlib
p = pathlib.Path('main.py')
t = p.read_text()

# Add style handling right after prompt is defined
old = '        prompt = message.content[len("!aiimage"):].strip()'
new = '''        prompt = message.content[len("!aiimage"):].strip()
        style_suffix = ""
        if prompt.lower().startswith("anime "):
            prompt = prompt[6:].strip()
            style_suffix = ", anime style, vibrant, detailed anime art"
        elif prompt.lower().startswith("realistic "):
            prompt = prompt[10:].strip()
            style_suffix = ", photorealistic, ultra detailed, 8k photo"
        elif prompt.lower().startswith("3d "):
            prompt = prompt[3:].strip()
            style_suffix = ", 3d render, pixar style, cute"
        prompt = prompt + style_suffix'''

if old in t:
    t = t.replace(old, new, 1)
    p.write_text(t)
    print("STYLE 1 ADDED!")
else:
    print("NOT FOUND - send screenshot of main.py")
