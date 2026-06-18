with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    if not u or not u.get('card_name'):
        await msg.answer(t('no_card', msg.from_user.id))'''

new = '''    logging.info(f"DEBUG my_card user_id={msg.from_user.id}")
    if not u or not u.get('card_name'):
        await msg.answer(t('no_card', msg.from_user.id))'''

if old in content:
    content = content.replace(old, new)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Debug log added to my_card_cmd.')
else:
    print('Pattern not found.')
