import asyncpg, asyncio, os
async def q():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL","postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"))
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
    print([r['column_name'] for r in cols])
    await conn.close()
asyncio.run(q())