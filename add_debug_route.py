import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

debug_route = '''
@app.get("/api/debug/user/{user_id}")
async def debug_user(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = \", user_id)
    if not row:
        return {"error": "User not found"}
    return dict(row)
'''

if '/api/debug/user/' not in content:
    # Insert before the line "if __name__ == '__main__':"
    main_pos = content.find("if __name__ == '__main__':")
    if main_pos != -1:
        content = content[:main_pos] + debug_route + '\n\n' + content[main_pos:]
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Debug route added.')
    else:
        print('ERROR: main block not found')
else:
    print('Debug route already exists.')
