import asyncpg, asyncio, os
async def fix():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"))
    cols = ["iwa_balance FLOAT DEFAULT 0", "points FLOAT DEFAULT 0", "role TEXT DEFAULT 'user'", "photo_file_id TEXT", "state TEXT DEFAULT 'IDLE'", "community_verified BOOLEAN DEFAULT FALSE"]
    for c in cols:
        col_name = c.split()[0]
        try:
            await conn.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {c}")
            print(f"OK: {col_name}")
        except Exception as e:
            print(f"SKIP: {col_name} - {e}")
    await conn.close()
asyncio.run(fix())
