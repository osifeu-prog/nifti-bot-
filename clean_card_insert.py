with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any existing /api/card endpoint (with its function body)
import re
# Pattern to match the endpoint and its body until next @app or #
content = re.sub(r'@app\.get\("/api/card/\{user_id\}"\).*?(?=\n@|\n#|\nif __name__|\Z)', '', content, flags=re.DOTALL)

# Insert clean endpoint after app = FastAPI(lifespan=lifespan)
endpoint_code = '''
@app.get("/api/card/{user_id}")
async def api_card_json(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT card_name, card_prof, wallet FROM users WHERE user_id = ", user_id)
    if not row:
        return {"card_name": "Guest", "card_prof": "", "wallet": ""}
    return {"card_name": row["card_name"], "card_prof": row["card_prof"], "wallet": row["wallet"]}
'''

insert_marker = 'app = FastAPI(lifespan=lifespan)'
content = content.replace(insert_marker, insert_marker + endpoint_code)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Clean endpoint inserted.')
