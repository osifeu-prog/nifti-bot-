import asyncio, json, os, asyncpg, logging, re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

DB_URL = os.getenv("DATABASE_URL")
pool = None
LANG = {}

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY, lang TEXT DEFAULT 'en',
                card_name TEXT, card_prof TEXT, wallet TEXT,
                price REAL DEFAULT 1, ref_id BIGINT,
                share_count INT DEFAULT 0, level TEXT DEFAULT 'free',
                minisite TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS promo_claims (
                user_id BIGINT UNIQUE, wallet TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT
            )
        """)
        await conn.execute("INSERT INTO settings VALUES ('free_cards_max','200'),('free_cards_claimed','0') ON CONFLICT DO NOTHING")
        # SaaS columns
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE")

def load_lang():
    global LANG
    with open("lang.json","r",encoding="utf-8") as f:
        LANG = json.load(f)

def t(key, lang):
    return LANG.get(lang, LANG["en"]).get(key, LANG["en"].get(key, key))

def platform_fee(amount):
    return round(amount * 0.2, 2)

def seller_amount(amount):
    return amount - platform_fee(amount)

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
    kb.add(t("create_card",lang), t("my_card",lang))
    kb.add(t("premium",lang), t("earnings",lang))
    kb.add(t("leaderboard",lang), t("settings_menu",lang), t("help",lang))
    return kb

def all_menu_labels(lang=None):
    if lang:
        return set(t(k, lang) for k in ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"])
    labels = set()
    for lang_code in LANG:
        labels.update(all_menu_labels(lang_code))
    return labels
