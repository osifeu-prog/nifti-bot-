import asyncio
from nifti_core import pool

async def main():
    async with pool.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM users WHERE user_id = ', 224223270)
        if row:
            print(dict(row))
        else:
            print('No user found')

asyncio.run(main())
