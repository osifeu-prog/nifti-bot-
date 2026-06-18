import asyncpg
import os

class DBManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))
        print("SAAS DB Pool initialized")

    async def get_user_wallet(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT wallet, iwa_balance FROM users WHERE user_id = $1", user_id)
