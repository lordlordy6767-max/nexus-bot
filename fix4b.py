import pathlib
p = pathlib.Path('main.py')
t = p.read_text()
old = 'prompt = message.content.replace("!aiimage", "", 1).strip()'
new = '''prompt = message.content.replace("!aiimage", "", 1).strip()
        style_suffix = ""
        if prompt.lower().startswith("anime "):
            prompt = prompt[6:].strip()
            style_suffix = ", anime style, vibrant, detailed anime art"
        prompt = prompt + style_suffix'''
if old in t:
    t = t.replace(old, new, 1)
    p.write_text(t)
    print("STYLE 1 ADDED!")
else:
    print("STILL NOT FOUND")
