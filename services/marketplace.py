"""
NIFTI Marketplace Service
Direct asyncpg access to existing DB tables.
"""
import asyncpg
import nifti_core as core

async def add_product(user_id: int, name: str, description: str, price: float) -> int:
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO products (name, description, price, active) VALUES ($1, $2, $3, TRUE) RETURNING id",
            name, description, price
        )
        # Associate with store
        await conn.execute(
            "INSERT INTO stores (user_id, store_name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, name
        )
        return row['id']

async def list_products(user_id: int = None, active_only: bool = True):
    async with core.pool.acquire() as conn:
        if user_id:
            rows = await conn.fetch(
                "SELECT p.* FROM products p JOIN stores s ON s.user_id = $1 WHERE p.active = $2",
                user_id, active_only
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM products WHERE active = $1",
                active_only
            )
        return [dict(r) for r in rows]

async def buy_product(buyer_user_id: int, product_id: int, referrer_user_id: int = None):
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            # Get product
            product = await conn.fetchrow("SELECT * FROM products WHERE id = $1 AND active = TRUE", product_id)
            if not product:
                return {"ok": False, "error": "Product not found"}

            # Get buyer balance
            buyer = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", buyer_user_id)
            if not buyer or buyer['balance'] < product['price']:
                return {"ok": False, "error": "Insufficient balance"}

            # Deduct buyer
            await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", product['price'], buyer_user_id)

            # Find seller via stores
            seller = await conn.fetchrow("SELECT user_id FROM stores WHERE store_name = $1", product['name'])
            seller_id = seller['user_id'] if seller else None

            # Calculate platform fee (20%)
            fee = round(product['price'] * 0.2, 2)
            seller_net = product['price'] - fee

            # Credit seller
            if seller_id:
                await conn.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", seller_net, seller_id)

            # Record purchase
            await conn.execute(
                "INSERT INTO purchases (buyer_user_id, product_id, referrer_user_id, amount_ton, commission_paid, status) VALUES ($1, $2, $3, $4, FALSE, 'completed')",
                buyer_user_id, product_id, referrer_user_id, product['price']
            )

            # Record transaction
            await conn.execute(
                "INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, 'purchase')",
                buyer_user_id, -product['price']
            )
            if seller_id:
                await conn.execute(
                    "INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, 'sale')",
                    seller_id, seller_net
                )

            # Commission for platform (if fee > 0)
            if fee > 0:
                await conn.execute(
                    "INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status) VALUES ($1, $2, $3, 0, 'pending')",
                    buyer_user_id, 0, fee  # to_user_id=0 represents platform
                )

            # Award XP
            await conn.execute(
                "INSERT INTO xp (user_id, xp) VALUES ($1, 10) ON CONFLICT (user_id) DO UPDATE SET xp = xp + 10",
                buyer_user_id
            )

            return {"ok": True, "product": product['name'], "price": product['price'], "fee": fee}

async def get_store(user_id: int):
    async with core.pool.acquire() as conn:
        store = await conn.fetchrow("SELECT * FROM stores WHERE user_id = $1", user_id)
        if not store:
            return None
        products = await conn.fetch("SELECT p.* FROM products p JOIN stores s ON s.user_id = $1 WHERE p.name = s.store_name", user_id)
        return {"store": dict(store), "products": [dict(p) for p in products]}

async def get_user_balance(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT balance FROM users WHERE user_id = $1", user_id)
        return float(row['balance']) if row else 0.0

async def add_balance(user_id: int, amount: float):
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = COALESCE(balance, 0) + $1 WHERE user_id = $2", amount, user_id)

