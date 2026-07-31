import json, re

posts = json.load(open('data/posts.json', encoding='utf-8'))
posts_str = json.dumps(posts, ensure_ascii=False, separators=(',',':')).replace('</', '<\\/')

with open('index.html', encoding='utf-8') as f:
    html = f.read()

pattern = re.compile(r'<script>\s*window\.__BRYCERIEL_POSTS__ = \[.*?\];\s*</script>', re.DOTALL)
matches = list(pattern.finditer(html))
for m in reversed(matches):
    html = html[:m.start()] + html[m.end():]

embed = '<script>\nwindow.__BRYCERIEL_POSTS__ = ' + posts_str + ';\n</script>\n'
html = html.replace('<body class="welcome-locked">', '<body class="welcome-locked">\n' + embed, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'index.html atualizado: {len(html)/1024/1024:.2f} MB, {len(posts)} posts')