import asyncpg

async def get_user_wallet(user_id: int):
    # נשתמש ב-user_id במקום ב-id ובשמות העמודות הנכונים
    query = "SELECT wallet, iwa_balance FROM users WHERE user_id = $1"
    # הערה: אם העמודה אצלך נקראת אחרת, שנה כאן את 'wallet'
    async with asyncpg.connect(os.getenv("DATABASE_URL")) as conn:
        return await conn.fetchrow(query, user_id)
