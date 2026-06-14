import asyncio, asyncpg, os
async def main():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    await conn.execute('DROP TABLE IF EXISTS users, products, invoices CASCADE')
    await conn.execute('''CREATE TABLE users (
        user_id BIGINT PRIMARY KEY,
        lang TEXT DEFAULT 'en',
        card_name TEXT,
        card_prof TEXT,
        wallet TEXT,
        price REAL DEFAULT 1,
        ref_id BIGINT
    )''')
    await conn.execute('''CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL,
        active BOOLEAN DEFAULT TRUE
    )''')
    await conn.execute('''CREATE TABLE invoices (
        id TEXT PRIMARY KEY,
        user_id BIGINT,
        product_id INT,
        amount REAL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    print('✅ DB ready')
    await conn.close()
asyncio.run(main())
