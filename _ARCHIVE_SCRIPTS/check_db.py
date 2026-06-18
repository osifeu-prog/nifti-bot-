import asyncpg, asyncio, os

async def check():
    url = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
    try:
        conn = await asyncpg.connect(url)
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        print("DB OK - tables:", [r['tablename'] for r in tables])
        await conn.close()
    except Exception as e:
        print("DB ERROR:", e)

asyncio.run(check())