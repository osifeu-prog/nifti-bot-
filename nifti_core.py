import asyncio, json, os, asyncpg, logging, re, time
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

DB_URL = os.getenv("DATABASE_URL")
pool = None
LANG = {}

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)
    logging.info(' DB pool created')

async def check_db_health():
    try:
        async with pool.acquire() as conn:
            start = time.monotonic()
            await conn.fetchval('SELECT 1')
            latency = (time.monotonic() - start) * 1000
            return {"status": "ok", "pool": "active", "latency_ms": round(latency, 2)}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

def load_lang():
    global LANG
    with open("lang.json", "r", encoding="utf-8") as f:
        LANG = json.load(f)

def t(key, lang):
    return LANG.get(lang, LANG["en"]).get(key, LANG["en"].get(key, key))

def platform_fee(amount):
    return round(amount * 0.2, 2)

def seller_amount(amount):
    return amount - platform_fee(amount)


async def get_nifti_index():
    async with pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        # Placeholder for volume (when transactions table exists)
        volume = await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')
        # Simple index formula
        index = round((users * 0.1 + cards * 0.5 + volume * 0.01), 2)
        return {
            'users': users,
            'cards': cards,
            'volume_tons': float(volume) if volume else 0,
            'index': index
        }

def is_valid_ton(address):
    if not address:
        return False
    address = str(address).strip()
    if not (address.startswith("UQ") or address.startswith("EQ")):
        return False
    if len(address) != 48:
        return False
    if not re.match(r"^[UE]Q[A-Za-z0-9_-]{46}$", address):
        return False
    return True

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

class EditForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

def main_menu(lang):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(t("create_card", lang), t("my_card", lang))
    kb.add(t("premium", lang), t("earnings", lang))
    kb.add(t("leaderboard", lang), t("settings_menu", lang), t("help", lang))
    return kb

def all_menu_labels(lang=None):
    if lang:
        return set(t(k, lang) for k in ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"])
    labels = set()
    for lang_code in LANG:
        labels.update(all_menu_labels(lang_code))
    return labels
import aiohttp

TONCENTER_API = "https://toncenter.com/api/v2"

async def verify_boc(tx_hash: str) -> bool:
    """Check if a transaction exists and is valid on TON."""
    url = f"{TONCENTER_API}/getTransactions?hash={tx_hash}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("ok", False)
    return False
import aiohttp
import os

TONCENTER_API = "https://toncenter.com/api/v2"

async def verify_boc(tx_hash: str) -> dict:
    """Check transaction on TON. Returns dict with ok, amount, sender, comment or error."""
    url = f"{TONCENTER_API}/getTransactions?hash={tx_hash}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    tx = data.get("result", [{}])[0]
                    value = int(tx.get("in_msg", {}).get("value", 0)) / 1e9
                    comment = tx.get("comment", "")
                    sender = tx.get("in_msg", {}).get("source", "")
                    return {"ok": True, "amount": value, "sender": sender, "comment": comment}
                return {"ok": False, "error": "Transaction not found or invalid"}
            return {"ok": False, "error": f"API error {resp.status}"}



import aiohttp
import os

TONCENTER_API = "https://toncenter.com/api/v2"

async def verify_boc(tx_hash: str) -> dict:
    """Check transaction on TON. Returns dict with ok, amount, sender, comment or error."""
    url = f"{TONCENTER_API}/getTransactions?hash={tx_hash}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    tx = data.get("result", [{}])[0]
                    value = int(tx.get("in_msg", {}).get("value", 0)) / 1e9
                    comment = tx.get("comment", "")
                    sender = tx.get("in_msg", {}).get("source", "")
                    return {"ok": True, "amount": value, "sender": sender, "comment": comment}
                return {"ok": False, "error": "Transaction not found or invalid"}
            return {"ok": False, "error": f"API error {resp.status}"}
