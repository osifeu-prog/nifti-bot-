with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'fetchrow("SELECT card_name, card_prof, wallet FROM users WHERE user_id = ", user_id)'
new = 'fetchrow("SELECT card_name, card_prof, wallet FROM users WHERE user_id = \", user_id)'

if old in content:
    content = content.replace(old, new)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SQL placeholder fixed.')
else:
    print('Old string not found  already fixed?')
