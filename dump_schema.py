import asyncpg, asyncio, os

async def dump():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"))
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    for t in tables:
        print(f"\n-- TABLE {t['tablename']}")
        cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=$1", t['tablename'])
        for c in cols:
            print(f"    {c['column_name']} {c['data_type']}")
    await conn.close()

asyncio.run(dump())
