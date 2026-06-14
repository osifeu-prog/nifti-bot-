import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    async with pool.acquire() as conn:
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS minisite TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE")
    yield
    if pool:
        await pool.close()

app = FastAPI(lifespan=lifespan)

@app.get("/card/{user_id}", response_class=HTMLResponse)
async def user_card(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT card_name, card_prof, wallet, minisite FROM users WHERE user_id=$1", user_id
        )
    if not row:
        return HTMLResponse("<h1>Card not found</h1>", status_code=404)
    name = row["card_name"] or "Unknown"
    prof = row["card_prof"] or ""
    wallet = row["wallet"] or "No wallet"
    minisite = row["minisite"] or ""
    html = f"""<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"><title>{name}  NIFTI Card</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font-family: Arial; background: #111; color: #fff; padding: 20px; text-align: center; }}
.card {{ background: #222; border-radius: 12px; padding: 20px; max-width: 400px; margin: 0 auto; }}
</style></head>
<body>
<div class="card">
<h1>{name}</h1>
<p>{prof}</p>
<p>💎 Wallet: <code>{wallet}</code></p>
{"<p><a href='" + minisite + "'>Mini-Site</a></p>" if minisite else ""}
</div>
<p>Powered by NIFTI</p>
</body></html>"""
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
