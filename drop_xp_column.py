import asyncpg, asyncio, os
async def main():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL', 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main'))
    await conn.execute("ALTER TABLE users DROP COLUMN IF EXISTS xp")
    print("xp column dropped from users")
    await conn.close()
asyncio.run(main())
