import asyncio
from engine import engine

async def init():
    await engine.start()

    await engine.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username TEXT,
        first_seen TIMESTAMP DEFAULT NOW()
    )
    """)

    print("[DB] USERS TABLE READY")

    await engine.close()

asyncio.run(init())

