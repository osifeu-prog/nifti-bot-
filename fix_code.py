import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ??? ??????? ?-Regex ??? ????? ?? ????? ??????? ????? ?????
# ????? ?????? ?-u = await... ??????? ?-if not u or not u.get...
pattern = r"u = await conn\.fetchrow\('SELECT \* FROM users WHERE user_id=\', msg\.from_user\.id\)\n\n\s+if not u or not u\.get\('card_name'\):"

replacement = """row = await conn.fetchrow('SELECT * FROM users WHERE user_id=', msg.from_user.id)
    u = dict(row) if row else None

    if not u or not u.get('card_name'):"""

new_content = re.sub(pattern, replacement, content)

if new_content != content:
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS: Logic fixed.')
else:
    print('ERROR: Pattern not found. Check if the code was already changed.')
