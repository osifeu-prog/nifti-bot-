import asyncio, asyncpg, os

async def main():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    await conn.execute('CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT, description TEXT, price REAL, active BOOLEAN DEFAULT TRUE)')
    await conn.execute('CREATE TABLE IF NOT EXISTS stores (id SERIAL PRIMARY KEY, user_id BIGINT, store_name TEXT, description TEXT, created_at TIMESTAMPTZ DEFAULT NOW())')
    await conn.execute('CREATE TABLE IF NOT EXISTS purchases (id BIGSERIAL PRIMARY KEY, buyer_user_id BIGINT, product_id INTEGER, referrer_user_id BIGINT, amount_ton NUMERIC, commission_paid BOOLEAN DEFAULT FALSE, tx_hash TEXT, invoice_id TEXT, status TEXT DEFAULT ''pending'', created_at TIMESTAMP DEFAULT NOW())')
    await conn.execute('CREATE TABLE IF NOT EXISTS transactions (id SERIAL PRIMARY KEY, user_id BIGINT, amount DOUBLE PRECISION, type VARCHAR(50), timestamp TIMESTAMP DEFAULT NOW())')
    await conn.execute('CREATE TABLE IF NOT EXISTS commissions (id BIGSERIAL PRIMARY KEY, from_user_id BIGINT, to_user_id BIGINT, amount_ton NUMERIC, level INTEGER, status TEXT DEFAULT ''pending'', purchase_id BIGINT, created_at TIMESTAMP DEFAULT NOW())')
    await conn.execute('CREATE TABLE IF NOT EXISTS xp (user_id BIGINT PRIMARY KEY, xp INTEGER DEFAULT 0, badge TEXT)')
    await conn.execute("INSERT INTO products (name, description, price) VALUES ('SIF Token Sample','A demonstration product',5.0) ON CONFLICT DO NOTHING")
    await conn.execute("INSERT INTO stores (user_id, store_name) VALUES (224223270,'SIF Token Sample') ON CONFLICT DO NOTHING")
    await conn.close()
    print('Done')

asyncio.run(main())
