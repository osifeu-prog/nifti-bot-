with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ??? ?? ????? ?? ?-endpoint
card_start = None
for i, line in enumerate(lines):
    if line.strip().startswith('@app.get("/api/card/{user_id}")'):
        card_start = i
        break

if card_start is None:
    print('ERROR: endpoint not found')
    exit(1)

# ??? ?? ??? ???????? (????? ????? / ????? / ???? ???)
card_end = card_start
for j in range(card_start, len(lines)):
    if lines[j].strip() == '' or lines[j].strip().startswith('#') or lines[j].strip().startswith('@app.'):
        card_end = j
        break
else:
    card_end = len(lines)

# ??? ?? ?????
card_block = lines[card_start:card_end]

# ??? ?? ????? ??????
new_lines = lines[:card_start] + lines[card_end:]

# ??? ?? 'if __name__ == '__main__':'
main_pos = None
for i, line in enumerate(new_lines):
    if line.strip().startswith("if __name__ == '__main__':"):
        main_pos = i
        break

if main_pos is None:
    print('ERROR: if __name__ not found')
    exit(1)

# ???? ?? ????? ???? if __name__
new_lines = new_lines[:main_pos] + ['\n'] + card_block + ['\n'] + new_lines[main_pos:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('SUCCESS: /api/card moved before uvicorn.run')
