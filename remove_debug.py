import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'@app\.get\("/api/debug/user/\{user_id\}"\).*?return dict\(row\)\n', '', content, flags=re.DOTALL)
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Debug route removed.')
