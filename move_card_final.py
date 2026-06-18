import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the /api/card block
card_pattern = r'@app\.get\("/api/card/\{user_id\}"\)\n(?:.*\n)*?return \{.*?\}'
card_match = re.search(card_pattern, content)
if not card_match:
    print('ERROR: /api/card endpoint not found')
    exit(1)
card_code = card_match.group()

# Remove it from where it is now
content = content.replace(card_code, '')

# Insert before the line "if __name__ == '__main__':"
main_pos = content.find("if __name__ == '__main__':")
if main_pos == -1:
    print('ERROR: if __name__ not found')
    exit(1)

new_content = content[:main_pos] + '\n' + card_code + '\n\n' + content[main_pos:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('SUCCESS: /api/card moved before uvicorn.run')
