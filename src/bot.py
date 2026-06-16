import asyncio, json, os, asyncpg, logging, re, time
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())
DB_URL = os.getenv("DATABASE_URL")
pool = None
LANG = {}
ADMIN_ID = int(os.getenv("ADMIN_USER_ID", "0"))

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

def load_lang():
    global LANG
    with open("lang.json","r",encoding="utf-8") as f:
        LANG = json.load(f)

def t(key, lang):
    return LANG.get(lang, LANG["en"]).get(key, LANG["en"].get(key, key))

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

# ================== GLOBAL CANCEL  FIRST HANDLER (state='*') ==================
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_cmd(msg: types.Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.finish()
        lang = "en"
        async with pool.acquire() as conn:
            u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
            if u: lang = u["lang"]
        await msg.answer(t("cancel_msg", lang), reply_markup=main_menu(lang))
    else:
        await msg.answer("No active process to cancel.")

# ================== /start ==================
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() else None
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
        if ref and ref != msg.from_user.id:
            await conn.execute("INSERT INTO users (user_id,lang,ref_id) VALUES ($1,'en',$2) ON CONFLICT DO NOTHING", msg.from_user.id, ref)
        else:
            await conn.execute("INSERT INTO users (user_id,lang) VALUES ($1,'en') ON CONFLICT DO NOTHING", msg.from_user.id)
    kb = InlineKeyboardMarkup(row_width=2)
    for code, label in [("he","???? ?????"),("en","???? English"),("ru","???? ???????"),("ar","???? ???????"),("fr","???? Français"),("es","???? Español"),("zh","???? ??"),("pt","???? Português")]:
        kb.insert(InlineKeyboardButton(label, callback_data=f"lang_{code}"))
    await msg.answer(t("choose_lang","en"), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET lang=$1 WHERE user_id=$2", lang, call.from_user.id)
    await call.message.edit_text(t("welcome",lang))
    await call.message.answer(t("help_text",lang), reply_markup=main_menu(lang))
    await call.answer()

# ================== /guide ==================
@dp.message_handler(commands=['guide'])
async def guide(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    await msg.answer(t("mission_story",lang), parse_mode="HTML")

# ================== /settings ==================
@dp.message_handler(commands=['settings'])
async def settings_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(t("edit_name",lang), callback_data="edit_name"))
    kb.add(InlineKeyboardButton(t("edit_prof",lang), callback_data="edit_prof"))
    kb.add(InlineKeyboardButton(t("edit_wallet",lang), callback_data="edit_wallet"))
    kb.add(InlineKeyboardButton(t("edit_price",lang), callback_data="edit_price"))
    kb.add(InlineKeyboardButton(t("change_language",lang), callback_data="change_lang_menu"))
    kb.add(InlineKeyboardButton(t("view_stats",lang), callback_data="view_stats"))
    await msg.answer(t("settings_title",lang), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "edit_name")
async def edit_name_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t("card_name","en"))
    await EditForm.waiting_name.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "edit_prof")
async def edit_prof_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t("card_prof","en"))
    await EditForm.waiting_prof.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "edit_wallet")
async def edit_wallet_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t("card_wallet","en"))
    await EditForm.waiting_wallet.set()
    await call.answer()

@dp.message_handler(state=EditForm.waiting_name)
async def process_edit_name(msg: types.Message, state: FSMContext):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET card_name=$1 WHERE user_id=$2", msg.text, msg.from_user.id)
    await msg.answer(t("name_updated","en"))
    await state.finish()

@dp.message_handler(state=EditForm.waiting_prof)
async def process_edit_prof(msg: types.Message, state: FSMContext):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET card_prof=$1 WHERE user_id=$2", msg.text, msg.from_user.id)
    await msg.answer(t("prof_updated","en"))
    await state.finish()

@dp.message_handler(state=EditForm.waiting_wallet)
async def process_edit_wallet(msg: types.Message, state: FSMContext):
    if not re.match(r"^[UE]Q[A-Za-z0-9_-]{46}$", msg.text.strip()):
        await msg.answer(t("invalid_wallet","en"))
        return
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET wallet=$1 WHERE user_id=$2", msg.text.strip(), msg.from_user.id)
    await msg.answer(t("wallet_updated","en"))
    await state.finish()

# ================== /share ==================
@dp.message_handler(commands=['share'])
async def share_card(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang,card_name FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
        if not u or not u["card_name"]:
            await msg.answer(t("no_card",lang))
            return
    link = f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("?? Telegram", url=f"https://t.me/share/url?url={link}"))
    kb.add(InlineKeyboardButton("?? WhatsApp", url=f"https://wa.me/?text={link}"))
    kb.add(InlineKeyboardButton("?? LinkedIn", url=f"https://www.linkedin.com/sharing/share-offsite/?url={link}"))
    kb.add(InlineKeyboardButton("?? Twitter/X", url=f"https://twitter.com/intent/tweet?url={link}"))
    await msg.answer(t("share_message",lang).format(link=link), reply_markup=kb)

# ================== /setprice ==================
@dp.message_handler(commands=['setprice'])
async def set_price(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang,price FROM users WHERE user_id=$1", msg.from_user.id)
        if not u: await msg.answer("Please /start first."); return
        lang = u["lang"]
        parts = msg.get_args().split()
        if parts:
            try:
                price = float(parts[0])
                await conn.execute("UPDATE users SET price=$1 WHERE user_id=$2", price, msg.from_user.id)
                await msg.answer(t("setprice_done",lang).format(price=price))
            except:
                await msg.answer(t("setprice_invalid",lang))
        else:
            await msg.answer(t("setprice_prompt",lang).format(price=u["price"]))

# ================== /market ==================
@dp.message_handler(commands=['market'])
async def market_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        sellers = await conn.fetch("SELECT card_name,price FROM users WHERE card_name IS NOT NULL AND price>0 LIMIT 10")
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    rows = "\n".join(f"{s['card_name']}  {s['price']} TON" for s in sellers) if sellers else t("market_empty",lang)
    await msg.answer(t("market",lang).format(sellers=rows))

# ================== /myreferrals ==================
@dp.message_handler(commands=['myreferrals'])
async def myreferrals_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang,share_count FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
        refs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE ref_id=$1 AND card_name IS NOT NULL", msg.from_user.id)
    await msg.answer(t("myreferrals",lang).format(refs=refs,pts=refs) + f"\n?? Shares: {u['share_count'] if u else 0}")

# ================== /status ==================
@dp.message_handler(commands=['status'])
async def status_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    await msg.answer(t("status",lang).format(users=users, cards=cards, purchases=0, pending=0, events=0))

# ================== /feedback ==================
@dp.message_handler(commands=['feedback'])
async def feedback_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    await msg.answer(t("feedback_sent",lang))

# ================== /my_card ==================
@dp.message_handler(commands=['my_card'])
async def my_card_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
        if not u or not u["card_name"]:
            await msg.answer(t("no_card",lang))
            return
        info = t("my_card_info",lang).format(name=u["card_name"], prof=u["card_prof"] or "", wallet=u["wallet"] or "", link=f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}")
        await msg.answer(info, parse_mode="HTML")

# ================== /broadcast (admin) ==================
@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("? Admin only"); return
    text = msg.get_args()
    if not text:
        await msg.answer("Usage: /broadcast <message>"); return
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users")
    sent, failed = 0, 0
    for r in rows:
        try:
            await bot.send_message(r["user_id"], text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await msg.answer(f"? Broadcast: {sent} sent, {failed} failed")

# ================== /minisite ==================
@dp.message_handler(commands=['minisite'])
async def minisite_cmd(msg: types.Message):
    url = msg.get_args().strip()
    if not url:
        await msg.answer("Usage: /minisite <url>"); return
    async with pool.acquire() as conn:
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS minisite TEXT")
        await conn.execute("UPDATE users SET minisite=$1 WHERE user_id=$2", url, msg.from_user.id)
    await msg.answer(f"? Mini-site: {url}")

# ================== /connect & /wallet ==================
@dp.message_handler(commands=['connect'])
async def connect_wallet(msg: types.Message):
    await msg.answer("?? Connect TON Wallet\n1. Open Tonkeeper\n2. Copy address (UQ...)\n3. Send: /wallet YOUR_ADDRESS", disable_web_page_preview=True)

@dp.message_handler(commands=['wallet'])
async def set_wallet(msg: types.Message):
    args = msg.get_args().split()
    if not args: await msg.answer("Usage: /wallet YOUR_TON_ADDRESS"); return
    addr = args[0].strip()
    if not re.match(r"^[UE]Q[A-Za-z0-9_-]{46}$", addr): await msg.answer("? Invalid TON address"); return
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO wallets (user_id, address, verified) VALUES ($1,$2,FALSE) ON CONFLICT (user_id) DO UPDATE SET address=$2", msg.from_user.id, addr)
    await msg.answer(f"? Wallet connected!\n{addr}")

# ================== /testsuite ==================
@dp.message_handler(commands=['testsuite'])
async def test_suite(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer("? Admin only"); return
    required = ["welcome","choose_lang","create_card","my_card","premium","earnings","leaderboard","help","settings_menu",
                "card_name","card_prof","card_wallet","card_done","my_card_info","no_card","setprice_prompt","setprice_done",
                "market","market_empty","salesboard","guide","feedback_sent","help_text","myreferrals","status",
                "mission_story","share_message","settings_title","edit_name","edit_prof","edit_wallet","edit_price",
                "change_language","view_stats","level_up","name_updated","prof_updated","wallet_updated","invalid_wallet","cancel_msg"]
    missing = []
    for lang in LANG:
        for key in required:
            if key not in LANG[lang]:
                missing.append(f"{lang}:{key}")
    if missing:
        await msg.answer(f"? Missing: {', '.join(missing[:10])}...")
    else:
        await msg.answer("? All languages complete!")

# ================== /commands ==================
@dp.message_handler(commands=['commands'])
async def list_commands(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer("? Admin only"); return
    await msg.answer("""?? All Commands
/start  Choose language
/settings  Edit profile
/share  Share your card
/guide  Our mission
/setprice  Set your price
/market  Price marketplace
/myreferrals  Your referrals
/status  Bot statistics
/feedback  Send feedback
/cancel  Cancel any process
/broadcast  Message all users
/minisite  Set your mini-site
/testsuite  Translation audit
/commands  This list""")

# ================== /claim ==================
@dp.message_handler(commands=['claim'])
async def claim_free_card(msg: types.Message):
    args = msg.get_args().split()
    if not args or args[0].upper() != "NIFTI200":
        await msg.answer("Invalid promo code. Use /claim NIFTI200"); return
    async with pool.acquire() as conn:
        async with conn.transaction():
            max_cards = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_max' FOR UPDATE"))
            claimed = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_claimed' FOR UPDATE"))
            if claimed >= max_cards: await msg.answer("All free cards claimed!"); return
            already = await conn.fetchval("SELECT COUNT(*) FROM promo_claims WHERE user_id=$1", msg.from_user.id)
            if already: await msg.answer("You already claimed a free card."); return
            await conn.execute("UPDATE settings SET value = CAST(CAST(value AS int) + 1 AS text) WHERE key='free_cards_claimed'")
            await conn.execute("INSERT INTO promo_claims (user_id, wallet) VALUES ($1, NULL)", msg.from_user.id)
            await msg.answer("? Free card activated!")

# ================== CARD CREATION (FSM)  blocks commands ==================
@dp.message_handler(lambda m: m.text in [t("create_card", l) for l in LANG])
async def create_card_kb(msg: types.Message, state: FSMContext):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    await msg.answer(t("card_name", lang))
    await state.set_state(CardForm.waiting_name)
    await state.update_data(lang=lang)

@dp.message_handler(state=CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    data = await state.get_data()
    await msg.answer(t("card_prof", data["lang"]))
    await state.set_state(CardForm.waiting_prof)

@dp.message_handler(state=CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    await state.update_data(prof=msg.text)
    data = await state.get_data()
    await msg.answer(t("card_wallet", data["lang"]))
    await state.set_state(CardForm.waiting_wallet)

@dp.message_handler(state=CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    wallet = msg.text.strip()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET card_name=$1, card_prof=$2, wallet=$3 WHERE user_id=$4",
                           data["name"], data["prof"], wallet, msg.from_user.id)
    link = f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}"
    await msg.answer(t("card_done", lang).format(link=link))
    await state.finish()

async def main():
    await create_pool()
    load_lang()
    logging.info("? Bot started")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())

