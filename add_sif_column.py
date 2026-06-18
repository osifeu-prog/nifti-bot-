import asyncpg, asyncio, os
async def add_sif():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL', 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main'))
    await conn.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS sif_balance FLOAT DEFAULT 0')
    await conn.execute('UPDATE users SET sif_balance = 0 WHERE sif_balance IS NULL')
    print('sif_balance column ready')
    await conn.close()
asyncio.run(add_sif())
