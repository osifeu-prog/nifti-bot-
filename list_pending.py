import asyncio, asyncpg, os

async def show():
    pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'), server_settings={'client_encoding': 'UTF8'})
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.invoice_id, p.amount_ton, p.created_at, pr.name
            FROM purchases p
            JOIN premium_products pr ON p.product_id = pr.id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        """)
        if not rows:
            print('No pending purchases.')
        else:
            print('📋 Pending purchases:')
            for r in rows:
                print(f'{r["invoice_id"]}  |  {r["amount_ton"]} TON  |  {r["name"]}  |  {r["created_at"]}')
    await pool.close()

asyncio.run(show())
