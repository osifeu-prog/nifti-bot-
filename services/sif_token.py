"""
SIF Token Management
- Buy SIF with TON (admin sets rate)
- Transfer SIF between users
- Check balance
"""
import asyncpg
import nifti_core as core

# Default conversion: 1 TON = 10 SIF
SIF_RATE = 10.0

async def get_sif_rate():
    return SIF_RATE

async def set_sif_rate(new_rate: float):
    global SIF_RATE
    SIF_RATE = new_rate
    return SIF_RATE

async def get_sif_balance(user_id: int) -> float:
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow('SELECT sif_balance FROM users WHERE user_id = $1', user_id)
        return float(row['sif_balance']) if row and row['sif_balance'] else 0.0

async def add_sif_balance(user_id: int, amount: float):
    async with core.pool.acquire() as conn:
        await conn.execute(
            'UPDATE users SET sif_balance = COALESCE(sif_balance, 0) + $1 WHERE user_id = $2',
            amount, user_id
        )

async def buy_sif(user_id: int, ton_amount: float):
    """Exchange TON for SIF at current rate."""
    if ton_amount <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            # Check TON balance
            bal = await conn.fetchval('SELECT balance FROM users WHERE user_id = $1', user_id)
            if bal is None or float(bal) < ton_amount:
                return {"ok": False, "error": "Insufficient TON balance"}
            # Deduct TON
            await conn.execute('UPDATE users SET balance = balance - $1 WHERE user_id = $2', ton_amount, user_id)
            # Calculate SIF amount
            sif_amount = round(ton_amount * SIF_RATE, 2)
            # Credit SIF
            await conn.execute(
                'UPDATE users SET sif_balance = COALESCE(sif_balance, 0) + $1 WHERE user_id = $2',
                sif_amount, user_id
            )
            return {"ok": True, "ton_spent": ton_amount, "sif_received": sif_amount, "rate": SIF_RATE}

async def sell_sif(user_id: int, sif_amount: float):
    """Exchange SIF back to TON at reverse rate."""
    if sif_amount <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            sif_bal = await conn.fetchval('SELECT sif_balance FROM users WHERE user_id = $1', user_id)
            if sif_bal is None or float(sif_bal) < sif_amount:
                return {"ok": False, "error": "Insufficient SIF balance"}
            await conn.execute(
                'UPDATE users SET sif_balance = sif_balance - $1 WHERE user_id = $2',
                sif_amount, user_id
            )
            ton_amount = round(sif_amount / SIF_RATE, 2)
            await conn.execute('UPDATE users SET balance = balance + $1 WHERE user_id = $2', ton_amount, user_id)
            return {"ok": True, "sif_sold": sif_amount, "ton_received": ton_amount, "rate": SIF_RATE}

async def transfer_sif(from_user_id: int, to_user_id: int, amount: float):
    if amount <= 0:
        return {"ok": False, "error": "Amount must be positive"}
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            from_bal = await conn.fetchval('SELECT sif_balance FROM users WHERE user_id = $1', from_user_id)
            if from_bal is None or float(from_bal) < amount:
                return {"ok": False, "error": "Insufficient SIF balance"}
            await conn.execute(
                'UPDATE users SET sif_balance = sif_balance - $1 WHERE user_id = $2',
                amount, from_user_id
            )
            await conn.execute(
                'UPDATE users SET sif_balance = COALESCE(sif_balance, 0) + $1 WHERE user_id = $2',
                amount, to_user_id
            )
            return {"ok": True, "from": from_user_id, "to": to_user_id, "amount": amount}
