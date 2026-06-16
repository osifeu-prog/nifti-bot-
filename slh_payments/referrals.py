"""
SLH Referral System.

Tracks referrals across all bots, calculates commissions,
and provides easy referral link generation.

Usage:
    from slh_payments.referrals import ReferralEngine, referral_engine
    link = referral_engine.get_link(user_id, "botshop")
    await referral_engine.track_referral(referrer_id, referred_id, "botshop")
"""
import os
import logging
from typing import Optional
from . import db

logger = logging.getLogger("slh.referrals")

# Commission rates (SLH points-based)
COMMISSION_RATE = 0.15  # 15% referral commission in SLH points
TIER2_RATE = 0.05       # 5% second-tier commission in SLH points

# Bot usernames for link generation
BOT_USERNAMES = {
    "botshop": "BotShop_bot",
    "wallet": "SLH_Wallet_bot",
    "factory": "SLH_Factory_bot",
    "academia": "SLH_Academia_bot",
    "guardian": "Grdian_bot",
    "community": "SLH_community_bot",
    "airdrop": "SLH_AIR_bot",
    "expertnet": "ExpertNetBot",
    "campaign": "SLH_Campaign_bot",
    "fun": "SLH_Fun_bot",
    "admin": "SLH_Admin_bot",
    "school": "SLH_School_bot",
    "nfty": "SLH_NFTY_bot",
    "match": "SLH_Match_bot",
    "wellness": "SLH_Wellness_bot",
    "tonmnh": "SLH_TonMnh_bot",
    "userinfo": "SLH_UserInfo_bot",
    "osif_shop": "OsifShop_bot",
    "repair": "SLH_Repair_bot",
}

# DB schema for referrals
REFERRAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    bot_name TEXT NOT NULL,
    status TEXT DEFAULT 'registered',  -- registered, converted, paid
    commission_amount NUMERIC(18,2) DEFAULT 0,
    commission_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(referred_id, bot_name)
);

CREATE TABLE IF NOT EXISTS referral_stats (
    user_id BIGINT NOT NULL,
    bot_name TEXT NOT NULL,
    total_referrals INT DEFAULT 0,
    converted_referrals INT DEFAULT 0,
    total_commission NUMERIC(18,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, bot_name)
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id);
"""


class ReferralEngine:
    """Manages referral tracking and commission calculation."""

    async def init_schema(self):
        """Create referral tables if they don't exist."""
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(REFERRAL_SCHEMA)

    def get_link(self, user_id: int, bot_name: str = "") -> str:
        """Generate a referral link for a user."""
        if bot_name and bot_name in BOT_USERNAMES:
            username = BOT_USERNAMES[bot_name]
            return f"https://t.me/{username}?start=ref_{user_id}"
        # Default: link to airdrop bot
        return f"https://t.me/SLH_AIR_bot?start=ref_{user_id}"

    def get_all_links(self, user_id: int) -> dict:
        """Generate referral links for all bots."""
        return {name: self.get_link(user_id, name) for name in BOT_USERNAMES}

    def parse_referral(self, start_param: str) -> Optional[int]:
        """Extract referrer ID from /start parameter."""
        if start_param and start_param.startswith("ref_"):
            try:
                return int(start_param[4:])
            except ValueError:
                pass
        return None

    async def track_referral(self, referrer_id: int, referred_id: int, bot_name: str) -> bool:
        """Record a new referral. Returns True if new."""
        if referrer_id == referred_id:
            return False
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    """INSERT INTO referrals (referrer_id, referred_id, bot_name)
                       VALUES ($1, $2, $3)
                       ON CONFLICT (referred_id, bot_name) DO NOTHING""",
                    referrer_id, referred_id, bot_name,
                )
                # Update stats
                await conn.execute(
                    """INSERT INTO referral_stats (user_id, bot_name, total_referrals)
                       VALUES ($1, $2, 1)
                       ON CONFLICT (user_id, bot_name)
                       DO UPDATE SET total_referrals = referral_stats.total_referrals + 1,
                                     updated_at = CURRENT_TIMESTAMP""",
                    referrer_id, bot_name,
                )
                logger.info("Referral tracked: %s -> %s (%s)", referrer_id, referred_id, bot_name)
                return True
            except Exception as e:
                logger.error("Failed to track referral: %s", e)
                return False

    async def mark_converted(self, referred_id: int, bot_name: str, payment_amount: float) -> bool:
        """Mark a referral as converted (user paid) and calculate commission."""
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT referrer_id FROM referrals WHERE referred_id=$1 AND bot_name=$2",
                referred_id, bot_name,
            )
            if not row:
                return False

            commission = round(payment_amount * COMMISSION_RATE, 2)
            await conn.execute(
                """UPDATE referrals SET status='converted', commission_amount=$3
                   WHERE referred_id=$1 AND bot_name=$2""",
                referred_id, bot_name, commission,
            )
            await conn.execute(
                """UPDATE referral_stats
                   SET converted_referrals = converted_referrals + 1,
                       total_commission = total_commission + $3,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE user_id=$1 AND bot_name=$2""",
                row["referrer_id"], bot_name, commission,
            )
            logger.info("Referral converted: user %s, commission %.2f", referred_id, commission)
            return True

    async def get_user_stats(self, user_id: int) -> dict:
        """Get referral stats for a user across all bots."""
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT bot_name, total_referrals, converted_referrals, total_commission
                   FROM referral_stats WHERE user_id=$1 ORDER BY total_referrals DESC""",
                user_id,
            )
            total_refs = sum(r["total_referrals"] for r in rows) if rows else 0
            total_converted = sum(r["converted_referrals"] for r in rows) if rows else 0
            total_commission = sum(float(r["total_commission"]) for r in rows) if rows else 0
        return {
            "total_referrals": total_refs,
            "converted": total_converted,
            "total_commission": total_commission,
            "by_bot": [dict(r) for r in rows],
        }

    async def get_referral_count(self, user_id: int, bot_name: str = "") -> int:
        """Get total referral count for a user."""
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            if bot_name:
                return await conn.fetchval(
                    "SELECT COALESCE(total_referrals, 0) FROM referral_stats WHERE user_id=$1 AND bot_name=$2",
                    user_id, bot_name,
                ) or 0
            return await conn.fetchval(
                "SELECT COALESCE(SUM(total_referrals), 0) FROM referral_stats WHERE user_id=$1",
                user_id,
            ) or 0

    def format_referral_card(self, user_id: int, bot_name: str = "", stats: dict = None) -> str:
        """Format a referral card message for the user."""
        link = self.get_link(user_id, bot_name) if bot_name else self.get_link(user_id)
        total = stats["total_referrals"] if stats else 0
        converted = stats["converted"] if stats else 0
        commission = stats["total_commission"] if stats else 0

        return (
            "ðŸ‘¥ *×”×”×¤× ×™×•×ª ×©×œ×š*\n\n"
            f"ï¿½- *×”×§×™×©×•×¨ ×”××™×©×™ ×©×œ×š:*\n`{link}`\n\n"
            f"ðŸ“Š ×”×¤× ×™×•×ª: {total}\n"
            f"âœ… ×”×¤× ×™×•×ª ×©×”×ž×™×¨×•: {converted}\n"
            f"ðŸ’° ×¢×ž×œ×”: {commission:.2f} × ×§×•×“×•×ª SLH\n\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "ðŸ’¡ *××™×š ×œ×”×¨×•×•×™ï¿½-?*\n"
            "1ï¸âƒ£ ×©×ª×£ ××ª ×”×§×™×©×•×¨ ×©×œ×š\n"
            "2ï¸âƒ£ ï¿½-×‘×¨×™× × ×¨×©×ž×™× ×“×¨×›×š\n"
            "3ï¸âƒ£ ×›×©×”× ×ž×©×“×¨×’×™× â€” ×ž×§×‘×œ 15% ×¢×ž×œ×” ×‘× ×§×•×“×•×ª SLH!\n\n"
            "ðŸŽ¯ ×”×–×ž×Ÿ 3 ï¿½-×‘×¨×™× = Community Premium ×‘ï¿½-×™× ×!\n\n"
            f"ðŸ“‹ *×©×ª×£ ×¢×›×©×™×•:* `{link}`"
        )

    def format_referral_footer(self, user_id: int, bot_name: str = "") -> str:
        """Short referral line to append to bot messages."""
        link = self.get_link(user_id, bot_name)
        return (
            f"\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            f"ðŸ‘¥ *×©×ª×£ ×•×”×¨×•×•×™ï¿½- 15% ×‘× ×§×•×“×•×ª SLH!*\n"
            f"ï¿½- `{link}`"
        )


# Global singleton
referral_engine = ReferralEngine()




