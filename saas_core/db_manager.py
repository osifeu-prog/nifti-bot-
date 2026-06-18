import asyncpg

class DBManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        # וודא שהחיבור נכון - השתמש בפרמטרים שלך
        self.pool = await asyncpg.create_pool(dsn='postgresql://postgres:postgres@localhost:5432/nifti')
        print("SAAS DB Pool initialized")

    async def get_user_wallet(self, user_id):
        async with self.pool.acquire() as conn:
            # תיקון השאילתה לשם העמודה הנכון (user_id)
            return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
