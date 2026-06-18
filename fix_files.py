# fix_files.py - run once to clean server.py and create marketplace.py
import os

# --- clean server.py ---
server_path = r"D:\NIFTI\server.py"
with open(server_path, "rb") as f:
    raw = f.read()
# remove BOM (U+FEFF) and null bytes
raw = raw.replace(b'\xef\xbb\xbf', b'').replace(b'\x00', b'')
with open(server_path, "wb") as f:
    f.write(raw)

# --- create marketplace.py ---
mp_content = """\"\"\"
NIFTI Marketplace Service
Direct asyncpg access to existing DB tables.
\"\"\"
import asyncpg
import nifti_core as core

async def add_product(user_id: int, name: str, description: str, price: float) -> int:
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO products (name, description, price, active) VALUES ($1, $2, $3, TRUE) RETURNING id",
            name, description, price
        )
        await conn.execute(
            "INSERT INTO stores (user_id, store_name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, name
        )
        return row['id']

async def list_products(active_only: bool = True):
    async with core.pool.acquire() as conn:
        return [dict(r) for r in await conn.fetch(
            "SELECT * FROM products WHERE active = $1", active_only
        )]

async def buy_product(buyer_user_id: int, product_id: int, referrer_user_id: int = None):
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            product = await conn.fetchrow("SELECT * FROM products WHERE id = $1 AND active = TRUE", product_id)
            if not product:
                return {"ok": False, "error": "Product not found"}
            buyer = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", buyer_user_id)
            if not buyer or buyer["balance"] < product["price"]:
                return {"ok": False, "error": "Insufficient balance"}
            fee = round(product["price"] * 0.2, 2)
            seller_net = product["price"] - fee
            await conn.execute(
                "UPDATE users SET balance = balance - $1 WHERE user_id = $2",
                product["price"], buyer_user_id
            )
            seller = await conn.fetchrow(
                "SELECT user_id FROM stores WHERE store_name = $1", product["name"]
            )
            if seller:
                await conn.execute(
                    "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
                    seller_net, seller["user_id"]
                )
            await conn.execute(
                "INSERT INTO purchases (buyer_user_id, product_id, referrer_user_id, amount_ton, commission_paid, status) VALUES ($1,$2,$3,$4,FALSE,'completed')",
                buyer_user_id, product_id, referrer_user_id, product["price"]
            )
            await conn.execute(
                "INSERT INTO xp (user_id, xp) VALUES ($1, 10) ON CONFLICT (user_id) DO UPDATE SET xp = xp + 10",
                buyer_user_id
            )
            return {"ok": True, "product": product["name"], "price": product["price"], "fee": fee}

async def get_store(user_id: int):
    async with core.pool.acquire() as conn:
        store = await conn.fetchrow("SELECT * FROM stores WHERE user_id = $1", user_id)
        if not store:
            return None
        products = await conn.fetch(
            "SELECT p.* FROM products p JOIN stores s ON s.user_id=$1 WHERE p.name=s.store_name", user_id
        )
        return {"store": dict(store), "products": [dict(p) for p in products]}

async def get_user_balance(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", user_id)
        return float(row['balance']) if row else 0.0

async def add_balance(user_id: int, amount: float):
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = COALESCE(balance, 0) + $1 WHERE user_id = $2", amount, user_id)
"""

mp_path = r"D:\NIFTI\services\marketplace.py"
with open(mp_path, "w", encoding="utf-8") as f:
    f.write(mp_content)

print("Both files fixed.")
