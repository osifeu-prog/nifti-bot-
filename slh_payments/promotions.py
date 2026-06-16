"""
SLH Promotions & Deals Engine.

Provides time-limited promotions, bundle deals, and seasonal discounts
that work across all bots in the ecosystem.

Usage:
    from slh_payments.promotions import PromoEngine
    promo = PromoEngine()
    deal = await promo.get_active_deal("botshop", user_id)
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from . import db

logger = logging.getLogger("slh.promotions")


@dataclass
class Deal:
    """A promotional deal."""
    code: str
    title_he: str
    title_en: str
    discount_pct: int  # 0-100
    bot_names: list  # which bots this applies to, empty = all
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_until: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    max_uses: int = 0  # 0 = unlimited
    current_uses: int = 0
    bundle: bool = False  # True = must buy all listed bots
    bundle_price_ils: float = 0.0
    bundle_price_ton: float = 0.0
    min_referrals: int = 0  # require X referrals to unlock

    @property
    def is_active(self) -> bool:
        now = datetime.utcnow()
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        return True

    @property
    def remaining_time(self) -> str:
        delta = self.valid_until - datetime.utcnow()
        if delta.total_seconds() <= 0:
            return "× ×’×ž×¨"
        days = delta.days
        hours = delta.seconds // 3600
        if days > 0:
            return f"{days} ×™×ž×™×, {hours} ×©×¢×•×ª"
        return f"{hours} ×©×¢×•×ª"


# â”€â”€â”€ Active Deals Catalog â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DEALS_CATALOG = [
    # ðŸ”¥ Launch deal - 30% off everything
    Deal(
        code="LAUNCH30",
        title_he="ðŸ”¥ ×ž×‘×¦×¢ ×”×©×§×”! 30% ×”× ï¿½-×” ×¢×œ ×›×œ ×”×‘×•×˜×™×",
        title_en="ðŸ”¥ Launch Deal! 30% off all bots",
        discount_pct=30,
        bot_names=[],  # all bots
        valid_from=datetime(2026, 4, 1),
        valid_until=datetime(2026, 5, 1),
        max_uses=100,
    ),
    # ðŸ’Ž Bundle deal - all 6 bots for 199â‚ª
    Deal(
        code="BUNDLE_ALL",
        title_he="ðŸ’Ž ï¿½-×‘×™×œ×” ×ž×œ××”! ×›×œ 6 ×”×‘×•×˜×™× ×‘×žï¿½-×™×¨ ×ž×™×•ï¿½-×“",
        title_en="ðŸ’Ž Full Bundle! All 6 bots at special price",
        discount_pct=0,
        bot_names=["botshop", "wallet", "factory", "academia", "guardian", "community"],
        bundle=True,
        bundle_price_ils=199.0,
        bundle_price_ton=10.0,
        valid_from=datetime(2026, 4, 1),
        valid_until=datetime(2026, 6, 1),
    ),
    # ðŸ¤ Refer-3 deal - free Community access
    Deal(
        code="REFER3_FREE",
        title_he="ðŸ¤ ×”×–×ž×Ÿ 3 ï¿½-×‘×¨×™× ×•×§×‘×œ Community Premium ×‘ï¿½-×™× ×!",
        title_en="ðŸ¤ Invite 3 friends & get Community Premium free!",
        discount_pct=100,
        bot_names=["community"],
        min_referrals=3,
        valid_from=datetime(2026, 4, 1),
        valid_until=datetime(2026, 12, 31),
    ),
    # ðŸŽ“ Student deal - Academia at 50% off
    Deal(
        code="STUDENT50",
        title_he="ðŸŽ“ ×ž×‘×¦×¢ ×¡×˜×•×“× ×˜×™×! 50% ×”× ï¿½-×” ×¢×œ Academia",
        title_en="ðŸŽ“ Student Deal! 50% off Academia",
        discount_pct=50,
        bot_names=["academia"],
        valid_from=datetime(2026, 4, 1),
        valid_until=datetime(2026, 9, 1),
    ),
    # ðŸ›¡ï¸ Guardian + Wallet bundle
    Deal(
        code="SECURE_PACK",
        title_he="ðŸ›¡ï¸ ï¿½-×‘×™×œ×ª ××‘×˜ï¿½-×”! Guardian + Wallet ×‘×žï¿½-×™×¨ ×ž×™×•ï¿½-×“",
        title_en="ðŸ›¡ï¸ Security Pack! Guardian + Wallet special price",
        discount_pct=0,
        bot_names=["guardian", "wallet"],
        bundle=True,
        bundle_price_ils=99.0,
        bundle_price_ton=5.0,
        valid_from=datetime(2026, 4, 1),
        valid_until=datetime(2026, 7, 1),
    ),
]


class PromoEngine:
    """Manages promotions across the SLH ecosystem."""

    def __init__(self):
        self.deals = DEALS_CATALOG

    def get_active_deals(self, bot_name: str = "") -> list:
        """Get all active deals, optionally filtered by bot."""
        active = [d for d in self.deals if d.is_active]
        if bot_name:
            active = [d for d in active if not d.bot_names or bot_name in d.bot_names]
        return active

    def get_deal_by_code(self, code: str) -> Optional[Deal]:
        """Find a deal by promo code."""
        code = code.upper().strip()
        for d in self.deals:
            if d.code == code and d.is_active:
                return d
        return None

    def calculate_price(self, deal: Deal, original_ils: float, original_ton: float) -> tuple:
        """Calculate discounted price. Returns (ils, ton)."""
        if deal.bundle:
            return deal.bundle_price_ils, deal.bundle_price_ton
        factor = 1 - (deal.discount_pct / 100)
        return round(original_ils * factor, 2), round(original_ton * factor, 2)

    def format_deals_message(self, bot_name: str = "", lang: str = "he") -> str:
        """Format active deals as a Telegram message."""
        deals = self.get_active_deals(bot_name)
        if not deals:
            if lang == "he":
                return "××™×Ÿ ×ž×‘×¦×¢×™× ×¤×¢×™×œ×™× ×›×¨×’×¢. ×¢×§×•×‘ ×ï¿½-×¨×™× ×• ×œ×¢×“×›×•× ×™×!"
            return "No active deals right now. Follow us for updates!"

        if lang == "he":
            lines = ["ðŸŽ‰ *×ž×‘×¦×¢×™× ×¤×¢×™×œ×™×*\n"]
            for d in deals:
                lines.append(f"*{d.title_he}*")
                if d.discount_pct > 0 and not d.bundle:
                    lines.append(f"  ðŸ’° ×”× ï¿½-×”: {d.discount_pct}%")
                if d.bundle:
                    lines.append(f"  ðŸ’° ×žï¿½-×™×¨ ï¿½-×‘×™×œ×”: {d.bundle_price_ils}â‚ª / {d.bundle_price_ton} TON")
                if d.min_referrals > 0:
                    lines.append(f"  ðŸ‘¥ ×“×¨×•×©: {d.min_referrals} ×”×¤× ×™×•×ª")
                lines.append(f"  â° × ×•×ª×¨: {d.remaining_time}")
                lines.append(f"  ðŸ·ï¸ ×§×•×“: `{d.code}`")
                lines.append("")
            lines.append("ðŸ’¡ ×©×œï¿½- /promo CODE ×œ×”×¤×¢×œ×”")
            return "\n".join(lines)
        else:
            lines = ["ðŸŽ‰ *Active Deals*\n"]
            for d in deals:
                lines.append(f"*{d.title_en}*")
                if d.discount_pct > 0 and not d.bundle:
                    lines.append(f"  ðŸ’° Discount: {d.discount_pct}%")
                if d.bundle:
                    lines.append(f"  ðŸ’° Bundle: {d.bundle_price_ils}â‚ª / {d.bundle_price_ton} TON")
                if d.min_referrals > 0:
                    lines.append(f"  ðŸ‘¥ Requires: {d.min_referrals} referrals")
                lines.append(f"  â° Time left: {d.remaining_time}")
                lines.append(f"  ðŸ·ï¸ Code: `{d.code}`")
                lines.append("")
            lines.append("ðŸ’¡ Send /promo CODE to activate")
            return "\n".join(lines)

    def format_upsell_footer(self, bot_name: str = "", user_id: int = 0) -> str:
        """Short promo line to append to bot responses."""
        deals = self.get_active_deals(bot_name)
        if not deals:
            return ""
        best = deals[0]
        return f"\n\nðŸ”¥ *{best.title_he}* â€” â° {best.remaining_time} | /deals"


# Global singleton
promo_engine = PromoEngine()




