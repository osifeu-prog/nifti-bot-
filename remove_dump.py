import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'@app\.get\("/api/dump/users"\).*?return \[dict\(r\) for r in rows\]\n', '', content, flags=re.DOTALL)
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Dump route removed.')
