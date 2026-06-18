# add_api_card.py
server_path = r"D:\NIFTI\server.py"

with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

new_route = """

@app.get("/api/card/{user_id}")
async def api_card_json(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT card_name, card_prof, wallet FROM users WHERE user_id = $1", user_id)
    if not row:
        return {"card_name": "Guest", "card_prof": "", "wallet": ""}
    return {"card_name": row["card_name"], "card_prof": row["card_prof"], "wallet": row["wallet"]}
"""

# Insert before the first '# ----------' after the last route
marker = "# ----------"
insert_pos = content.rfind(marker)
if insert_pos == -1:
    # fallback: insert before if __name__
    insert_pos = content.rfind("if __name__")
if insert_pos == -1:
    insert_pos = len(content)

content = content[:insert_pos] + new_route + "\n" + content[insert_pos:]

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)

print("API route added")
