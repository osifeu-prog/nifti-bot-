"""
SLH Internal Token Ledger
Fast, reliable token transfers without blockchain dependency.
Blockchain settlement can happen later.
"""
import os
import asyncpg
from typing import Optional

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        # Phase 0B (2026-04-21): unified fail-fast pool via shared_db_core.
        # max_size standardized 5â†’4.
        try:
            from shared_db_core import init_db_pool as _shared_init_db_pool
            _pool = await _shared_init_db_pool(
                os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"),
            )
        except Exception:
            _pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@postgres:5432/slh_main"),
                min_size=1, max_size=4,
            )
    return _pool


async def get_balance(user_id: int, token: str = "SLH") -> float:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2",
            user_id, token,
        )
    return float(row["balance"]) if row else 0.0


async def get_all_balances(user_id: int) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT token, balance FROM token_balances WHERE user_id=$1",
            user_id,
        )
    return {r["token"]: float(r["balance"]) for r in rows}


async def ensure_balance(user_id: int, token: str = "SLH"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO token_balances (user_id, token, balance)
               VALUES ($1, $2, 0) ON CONFLICT DO NOTHING""",
            user_id, token,
        )


async def transfer(from_uid: int, to_uid: int, token: str, amount: float,
                   memo: str = "", fee: float = 0) -> tuple:
    """
    Transfer tokens between users.
    Returns: (success, message, new_from_balance, new_to_balance)
    """
    if amount <= 0:
        return False, "×¡×›×•× ï¿½-×™×™×‘ ×œ×”×™×•×ª ï¿½-×™×•×‘×™", 0, 0
    if from_uid == to_uid:
        return False, "×œ× × ×™×ª×Ÿ ×œ×”×¢×‘×™×¨ ×œ×¢×¦×ž×š", 0, 0

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Check sender balance
            row = await conn.fetchrow(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2 FOR UPDATE",
                from_uid, token,
            )
            if not row or float(row["balance"]) < amount + fee:
                current = float(row["balance"]) if row else 0
                return False, f"×™×ª×¨×” ×œ× ×ž×¡×¤×§×ª ({current:.4f} {token})", current, 0

            # Ensure receiver has a balance row
            await conn.execute(
                "INSERT INTO token_balances (user_id, token, balance) VALUES ($1, $2, 0) ON CONFLICT DO NOTHING",
                to_uid, token,
            )

            # Deduct from sender
            await conn.execute(
                "UPDATE token_balances SET balance = balance - $3, updated_at = CURRENT_TIMESTAMP WHERE user_id=$1 AND token=$2",
                from_uid, token, amount + fee,
            )

            # Credit receiver
            await conn.execute(
                "UPDATE token_balances SET balance = balance + $3, updated_at = CURRENT_TIMESTAMP WHERE user_id=$1 AND token=$2",
                to_uid, token, amount,
            )

            # Record transfer
            await conn.execute(
                """INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, fee, memo, tx_type)
                   VALUES ($1, $2, $3, $4, $5, $6, 'transfer')""",
                from_uid, to_uid, token, amount, fee, memo,
            )

            # Get new balances
            from_bal = await conn.fetchval(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2", from_uid, token
            )
            to_bal = await conn.fetchval(
                "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2", to_uid, token
            )

    return True, "×”×¢×‘×¨×” ×‘×•×¦×¢×”!", float(from_bal), float(to_bal)


async def mint(user_id: int, token: str, amount: float, memo: str = "mint"):
    """Create tokens (admin only)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO token_balances (user_id, token, balance) VALUES ($1, $2, $3) ON CONFLICT (user_id, token) DO UPDATE SET balance = token_balances.balance + $3",
            user_id, token, amount,
        )
        await conn.execute(
            "INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type) VALUES (0, $1, $2, $3, $4, 'mint')",
            user_id, token, amount, memo,
        )


async def burn(user_id: int, token: str, amount: float, memo: str = "burn"):
    """Destroy tokens (admin only)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT balance FROM token_balances WHERE user_id=$1 AND token=$2", user_id, token
        )
        if not current or float(current) < amount:
            return False
        await conn.execute(
            "UPDATE token_balances SET balance = balance - $1 WHERE user_id=$2 AND token=$3",
            amount, user_id, token,
        )
        await conn.execute(
            "INSERT INTO token_transfers (from_user_id, to_user_id, token, amount, memo, tx_type) VALUES ($1, 0, $2, $3, $4, 'burn')",
            user_id, token, amount, memo,
        )
    return True


async def get_history(user_id: int, limit: int = 10) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, from_user_id, to_user_id, token, amount, fee, memo, tx_type, created_at
               FROM token_transfers
               WHERE from_user_id=$1 OR to_user_id=$1
               ORDER BY created_at DESC LIMIT $2""",
            user_id, limit,
        )
    return [dict(r) for r in rows]


async def get_leaderboard(token: str = "SLH", limit: int = 10) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, balance FROM token_balances WHERE token=$1 AND balance > 0 ORDER BY balance DESC LIMIT $2",
            token, limit,
        )
    return [dict(r) for r in rows]




