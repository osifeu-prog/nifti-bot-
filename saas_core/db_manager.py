import asyncpg
import os
from dotenv import load_dotenv

# טעינת המשתנים מהקובץ .env
load_dotenv(override=True)

class DBManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            raise ValueError("DATABASE_URL is not set in .env file!")
        
        print(f"Connecting to DB using URL from .env")
        self.pool = await asyncpg.create_pool(dsn=dsn)
        print("SAAS DB Pool initialized")

    async def get_user_wallet(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT wallet, iwa_balance FROM users WHERE user_id = $1", user_id)

# יצירת המופע שכל הקבצים ייבאו
db = DBManager()
