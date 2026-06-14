import os, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NIFTI_API")

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    logger.info("✅ FastAPI connected to PostgreSQL")
    yield
    if pool:
        await pool.close()
        logger.info("🛑 DB pool closed")

app = FastAPI(title="NIFTI SaaS API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    path = os.path.join("templates", "index.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Missing templates/index.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    if not pool:
        raise HTTPException(status_code=500, detail="DB pool not ready")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, card_name, card_prof, wallet, balance, is_premium FROM users WHERE user_id = $1",
            user_id
        )
    if not row:
        return {"exists": False, "user_id": user_id, "card_name": "Guest", "balance": 0.0, "is_premium": False}
    return {
        "exists": True,
        "user_id": row["user_id"],
        "card_name": row["card_name"],
        "card_prof": row["card_prof"],
        "wallet": row["wallet"],
        "balance": float(row["balance"]) if row["balance"] else 0.0,
        "is_premium": bool(row["is_premium"])
    }

@app.post("/api/verify_payment")
async def verify_payment(data: dict):
    user_id = data.get("user_id")
    boc = data.get("boc")
    if not user_id or not boc:
        return {"status": "error", "detail": "Missing user_id or boc"}
    # TODO: verify BOC against TON Center API
    # For now  mark as premium
    if pool:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE users SET is_premium = TRUE WHERE user_id = $1", user_id)
    return {"status": "success", "message": "Premium activated!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
