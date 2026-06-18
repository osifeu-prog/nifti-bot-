import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the /api/card endpoint and extract its code
card_pattern = r'(@app\.get\("/api/card/\{user_id\}"\)\n.*?(?=\n# |\nfrom |\napp\.mount|\n@app\.get|\nif __name__|\Z))'
card_match = re.search(card_pattern, content, re.DOTALL)
if not card_match:
    print('Error: /api/card endpoint not found.')
    exit(1)
card_code = card_match.group(1)
# Remove the block from its current location
content = content.replace(card_code, '')

# Remove everything after the uvicorn.run line (duplicate mounts, catch-all, etc.)
uvicorn_line = 'uvicorn.run(app, host=\'0.0.0.0\', port=port)'
uvicorn_idx = content.index(uvicorn_line) + len(uvicorn_line)
content = content[:uvicorn_idx] + '\n'

# Insert the card endpoint just before if __name__ == '__main__':
# Add a newline before insertion
insert_pos = content.index("if __name__ == '__main__':")
content = content[:insert_pos] + '\n' + card_code + '\n\n' + content[insert_pos:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Success: /api/card moved before uvicorn.run.')
