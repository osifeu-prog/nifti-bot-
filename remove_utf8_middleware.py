import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the add_utf8_header middleware (the whole block)
content = re.sub(
    r'@app\.middleware\("http"\)\s*async def add_utf8_header.*?return response\n',
    '',
    content,
    flags=re.DOTALL
)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('add_utf8_header middleware removed.')
