import asyncio, aiohttp, os, asyncpg, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
WALLET = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
TONCENTER_API = "https://toncenter.com/api/v2"
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
BOT_TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"

async def get_transactions():
    url = f"{TONCENTER_API}/getTransactions?address={WALLET}&limit=5"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("result", [])
    return []

async def send_telegram(user_id: int, text: str):
    import aiohttp
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": user_id, "text": text}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def process_tx(tx, pool):
    memo = tx.get("comment", "")
    if memo.startswith("NIFTI_PAY:"):
        user_id = int(memo.split(":")[1])
        value = int(tx["in_msg"]["value"]) / 1e9
        tx_hash = tx["transaction_id"]["hash"]
        async with pool.acquire() as conn:
            # Check if already processed
            exists = await conn.fetchval("SELECT tx_hash FROM premium_users WHERE tx_hash=$1", tx_hash)
            if exists:
                return
            await conn.execute("UPDATE users SET is_premium = TRUE WHERE user_id = $1", user_id)
            await conn.execute(
                "INSERT INTO premium_users (user_id, bot_name, amount, tx_hash) VALUES ($1, 'nifti', $2, $3)",
                user_id, value, tx_hash
            )
            logging.info(f"✅ Premium activated for user {user_id} ({value} TON)")
            # Notify user
            await send_telegram(user_id, f"🎉 Payment of {value} TON received! Your Premium status is now active.")
            # Notify admin (you)
            await send_telegram(224223270, f"💰 Payment received: {value} TON from user {user_id}")

async def main():
    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=2)
    logging.info("🔍 TON Scanner started (with notifications)")
    while True:
        try:
            txs = await get_transactions()
            for tx in txs:
                await process_tx(tx, pool)
        except Exception as e:
            logging.error(f"Scanner error: {e}")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())


