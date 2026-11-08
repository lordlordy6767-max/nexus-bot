import pathlib
p = pathlib.Path('main.py')
t = p.read_text()
added = []
if 'import urllib.parse' not in t:
    t = t.replace('import os', 'import os\nimport urllib.parse\nimport aiohttp\nimport io', 1)
    added.append('imports')
else:
    if 'import aiohttp' not in t:
        t = t.replace('import urllib.parse', 'import urllib.parse\nimport aiohttp', 1)
        added.append('aiohttp')
    if 'import io' not in t:
        t = t.replace('import aiohttp', 'import aiohttp\nimport io', 1)
        added.append('io')
p.write_text(t)
print('ADDED:', added if added else 'already had them')
