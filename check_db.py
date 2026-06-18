import asyncio, asyncpg, os

async def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return
    conn = await asyncpg.connect(db_url)
    row = await conn.fetchrow("SELECT * FROM users WHERE user_id = 224223270")
    if row:
        print("User found:")
        print(dict(row))
    else:
        print("User not found in DB")
    await conn.close()

asyncio.run(main())
