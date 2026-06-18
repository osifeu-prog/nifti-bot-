import asyncpg
import os

class DBManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main')
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.db_url)
        print('SAAS DB Pool initialized')

    async def get_user_data(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE id = ', user_id)

    async def close(self):
        await self.pool.close()
