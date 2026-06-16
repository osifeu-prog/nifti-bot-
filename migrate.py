import asyncio, asyncpg, os

async def migrate():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    # Stores table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL,
            store_name TEXT DEFAULT 'My Store',
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    # Payment methods table
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS payment_methods (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            method_type TEXT NOT NULL,  -- 'TON', 'BANK', 'PAYPAL'
            details TEXT NOT NULL,      -- wallet address, IBAN, etc.
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    # Products table (extends cards)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            payment_methods TEXT,  -- comma-separated method IDs or 'all'
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    print("✅ Migration complete: stores, payment_methods, products")
    await conn.close()

asyncio.run(migrate())
