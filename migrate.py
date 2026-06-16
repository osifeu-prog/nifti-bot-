import asyncio, asyncpg, os

async def migrate():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            ref_id BIGINT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            lang TEXT DEFAULT 'en',
            card_name TEXT,
            card_prof TEXT,
            wallet TEXT,
            price REAL DEFAULT 1.0,
            share_count INTEGER DEFAULT 0,
            level TEXT DEFAULT 'free',
            minisite TEXT,
            is_premium BOOLEAN DEFAULT FALSE,
            role TEXT DEFAULT 'user'
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            ref_id BIGINT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id)
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS premium_users (
            user_id BIGINT,
            bot_name TEXT,
            amount REAL,
            tx_hash TEXT PRIMARY KEY,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id SERIAL PRIMARY KEY,
            admin_id BIGINT,
            action TEXT,
            details TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    print("✅ Migration complete")
    await conn.close()

asyncio.run(migrate())
