import re
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

dump_route = r'''
@app.get("/api/dump/users")
async def dump_users():
    async with core.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users")
    return [dict(r) for r in rows]
'''

if '/api/dump/users' not in content:
    main_pos = content.find("if __name__ == '__main__':")
    if main_pos != -1:
        content = content[:main_pos] + dump_route + '\n\n' + content[main_pos:]
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Dump route added.')
    else:
        print('ERROR: main block not found')
else:
    print('Route already exists.')
