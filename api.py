import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    yield
    if pool:
        await pool.close()

app = FastAPI(lifespan=lifespan)

@app.get("/api/card/{user_id}")
async def get_card_json(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id=\", user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
