import asyncio, json, os, asyncpg, logging
from asyncpg.exceptions import SerializationError
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

DB_URL = os.getenv('DATABASE_URL')
pool = None
LANG = {}
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))

async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DB_URL)
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                lang TEXT DEFAULT 'en',
                card_name TEXT,
                card_prof TEXT,
                wallet TEXT,
                price REAL DEFAULT 1,
                ref_id BIGINT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT,
                description TEXT,
                price REAL,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                user_id BIGINT,
                product_id INT,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        # 200 free cards system
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS promo_claims (
                user_id BIGINT,
                wallet TEXT,
                claimed_at TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            INSERT INTO settings (key, value) VALUES ('free_cards_max', '200'), ('free_cards_claimed', '0')
            ON CONFLICT (key) DO NOTHING
        ''')

def load_lang():
    global LANG
    with open('lang.json', 'r', encoding='utf-8') as f:
        LANG = json.load(f)

def platform_fee(amount):
    return round(amount * 0.2, 2)

def seller_amount(amount):
    return amount - platform_fee(amount)


def is_valid_ton_address(address):
    """Basic TON address validation (UQ... or EQ..., length 48)"""
    if not address:
        return False
    address = address.strip()
    if not (address.startswith('UQ') or address.startswith('EQ')):
        return False
    if len(address) != 48:
        return False
    # allow base64url characters
    import re
    if not re.match(r'^[UE]Q[A-Za-z0-9_-]{46}
    return LANG.get(lang, LANG['en']).get(key, LANG['en'].get(key, key))

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

# /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for code, label in [('he','🇮🇱 עברית'),('en','🇬🇧 English'),('ru','🇷🇺 Русский'),
                        ('ar','🇸🇦 العربية'),('fr','🇫🇷 Français'),('es','🇪🇸 Español'),
                        ('zh','🇨🇳 中文'),('pt','🇧🇷 Português')]:
        keyboard.insert(InlineKeyboardButton(label, callback_data=f"lang_{code}"))
    await msg.answer(t('choose_lang', 'en'), reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split('_')[1]
    async with pool.acquire() as conn:
        await conn.execute("""INSERT INTO users (user_id, lang) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET lang=$2""", call.from_user.id, lang)
    await call.message.edit_text(t('welcome', lang))
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(t('create_card', lang), t('my_card', lang))
    kb.add(t('premium', lang), t('earnings', lang))
    kb.add(t('leaderboard', lang), t('help', lang))
    await call.message.answer(t('help_text', lang), reply_markup=kb)
    await call.answer()


@dp.message_handler(commands=['connect'])
async def connect_wallet(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=# /language', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    guide = (
        "🔗 <b>Connect Your TON Wallet</b>\n\n"
        "1. Open <a href='https://tonkeeper.com/'>Tonkeeper</a> or <a href='https://wallet.ton.org/'>TON Wallet</a>\n"
        "2. Copy your wallet address (starts with UQ...)\n"
        "3. Send it here: /wallet YOUR_ADDRESS\n\n"
        "Example: /wallet UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    )
    await msg.answer(guide, parse_mode='HTML', disable_web_page_preview=True)

# /language
@dp.message_handler(commands=['language'])
async def change_lang(msg: types.Message):
    await start(msg)

# /testsuite (admin)
@dp.message_handler(commands=['testsuite'])
async def test_suite(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    required_keys = ['welcome','choose_lang','create_card','my_card','premium','earnings','leaderboard','help',
                     'card_name','card_prof','card_wallet','card_done','my_card_info','no_card',
                     'setprice_prompt','setprice_done','market','salesboard','guide',
                     'feedback_sent','help_text','leaderboard_empty','leaderboard_msg',
                     'myreferrals','no_referrals','my_earnings','status','ref_earned',
                     'setprice_invalid','market_empty']
    report = "🔍 <b>Translation Audit</b>\n━━━━━━━━━━━━━\n"
    all_ok = True
    for lang in LANG:
        missing = [k for k in required_keys if k not in LANG[lang]]
        if missing:
            report += f"❌ {lang}: missing {', '.join(missing)}\n"
            all_ok = False
    if all_ok:
        report += "✅ All 8 languages have all required keys!\n"
    await msg.answer(report, parse_mode='HTML')

# /commands (admin)
@dp.message_handler(commands=['commands'])
async def list_commands(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    text = """🔧 <b>All Bot Commands</b>
━━━━━━━━━━━━━━━
/start  Choose language
/language  Change language
/testsuite  Translation audit
/claim  Claim free card
/simulate_purchase  Test platform fee
/setprice  Set your price
/market  Price marketplace
/salesboard  Sales leaderboard
/guide  How to earn
/myreferrals  Your referrals
/status  Bot statistics
/feedback  Send feedback
━━━━━━━━━━━━━━━
<b>Card Creation</b>
Use keyboard button to start.
━━━━━━━━━━━━━━━
<b>Admin</b>
/commands  This list
/verify invoice_id  Verify payment
"""
    await msg.answer(text, parse_mode='HTML')

# /claim NIFTI200
@dp.message_handler(commands=['claim'])
async def claim_free_card(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    args = msg.get_args().split()
    if not args or args[0].upper() != "NIFTI200":
        await msg.answer("Invalid promo code. Use /claim NIFTI200")
        return
    async with pool.acquire() as conn:
        async with conn.transaction():
            max_cards = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_max' FOR UPDATE"))
            claimed = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_claimed' FOR UPDATE"))
            if claimed >= max_cards:
                await msg.answer("All free cards claimed! Create a paid card now.")
                return
            already = await conn.fetchval("SELECT COUNT(*) FROM promo_claims WHERE user_id=$1", msg.from_user.id)
            if already:
                await msg.answer("You already claimed a free card.")
                return
            await conn.execute("UPDATE settings SET value = CAST(CAST(value AS int) + 1 AS text) WHERE key='free_cards_claimed'")
            await conn.execute("INSERT INTO promo_claims (user_id, wallet) VALUES ($1, 'none')", msg.from_user.id)
            await msg.answer("✅ Free card activated! Start sharing your link.")

# /simulate_purchase (admin)
@dp.message_handler(commands=['simulate_purchase'])
async def simulate_purchase(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    args = msg.get_args().split()
    if len(args) < 2:
        await msg.answer("Usage: /simulate_purchase <amount> <seller_id>")
        return
    try:
        amount = float(args[0])
        seller_id = int(args[1])
    except:
        await msg.answer("Invalid arguments")
        return
    fee = platform_fee(amount)
    seller_gets = seller_amount(amount)
    report = (f"<b>Simulated Purchase</b>\n"
              f"Amount: {amount} TON\n"
              f"Platform fee (20%): {fee} TON → Admin wallet\n"
              f"Seller receives: {seller_gets} TON")
    await msg.answer(report, parse_mode='HTML')

# --------------- CARD CREATION ---------------
@dp.message_handler(lambda m: m.text in sum([[LANG[l]['create_card']] for l in LANG], []))
async def create_card(msg: types.Message, state: FSMContext):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('card_name', lang))
    await state.set_state(CardForm.waiting_name)
    await state.update_data(lang=lang)

@dp.message_handler(state=CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    data = await state.get_data()
    await msg.answer(t('card_prof', data['lang']))
    await state.set_state(CardForm.waiting_prof)

@dp.message_handler(state=CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    await state.update_data(prof=msg.text)
    data = await state.get_data()
    await msg.answer(t('card_wallet', data['lang']))
    await state.set_state(CardForm.waiting_wallet)

@dp.message_handler(state=CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    wallet = msg.text.strip()
    async with pool.acquire() as conn:
        await conn.execute("""UPDATE users SET card_name=$1, card_prof=$2, wallet=$3 WHERE user_id=$4""",
                           data['name'], data['prof'], wallet, msg.from_user.id)
    link = f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}"
    await msg.answer(t('card_done', lang).format(link=link))
    await state.finish()


@dp.message_handler(commands=['wallet'])
async def set_wallet(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=# /my_card', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    args = msg.get_args().split()
    if not args:
        await msg.answer("Usage: /wallet YOUR_TON_ADDRESS")
        return
    address = args[0].strip()
    if not is_valid_ton_address(address):
        await msg.answer("❌ Invalid TON address. Must start with UQ... or EQ... and be 48 characters.")
        return
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO wallets (user_id, address, verified) VALUES (# /my_card, $2, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET address=$2, connected_at=NOW()
        """, msg.from_user.id, address)
    await msg.answer(f"✅ Wallet connected!\n<code>{address}</code>", parse_mode='HTML')

# /my_card
@dp.message_handler(lambda m: m.text in sum([[LANG[l]['my_card']] for l in LANG], []))
async def my_card(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
        if not u or not u['card_name']:
            await msg.answer(t('no_card', u['lang'] if u else 'en'))
            return
        lang = u['lang']
        info = t('my_card_info', lang).format(name=u['card_name'], prof=u['card_prof'],
                                              wallet=u['wallet'],
                                              link=f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}")
        await msg.answer(info, parse_mode='HTML')

# /setprice
@dp.message_handler(commands=['setprice'])
async def set_price(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang,price FROM users WHERE user_id=$1', msg.from_user.id)
        if not u:
            await msg.answer("Please /start first.")
            return
        lang = u['lang']
        parts = msg.get_args().split()
        if parts:
            try:
                price = float(parts[0])
                await conn.execute('UPDATE users SET price=$1 WHERE user_id=$2', price, msg.from_user.id)
                await msg.answer(t('setprice_done', lang).format(price=price))
            except:
                await msg.answer(t('setprice_invalid', lang))
        else:
            await msg.answer(t('setprice_prompt', lang).format(price=u['price']))

# /market
@dp.message_handler(commands=['market'])
async def market(msg: types.Message):
    async with pool.acquire() as conn:
        sellers = await conn.fetch("SELECT card_name,price FROM users WHERE card_name IS NOT NULL AND price>0 LIMIT 10")
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    rows = "\n".join(f"{s['card_name']}  {s['price']} TON" for s in sellers) if sellers else t('market_empty', lang)
    await msg.answer(t('market', lang).format(sellers=rows))

# /salesboard
@dp.message_handler(commands=['salesboard'])
async def salesboard(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('salesboard', lang).format(earners='...', sellers='...', rising='...'))

# /guide
@dp.message_handler(commands=['guide'])
async def guide(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('guide', lang))

# /feedback
@dp.message_handler(commands=['feedback'])
async def feedback(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('feedback_sent', lang))

# /myreferrals
@dp.message_handler(commands=['myreferrals'])
async def myreferrals(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
        refs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE ref_id=$1", msg.from_user.id)
    await msg.answer(t('myreferrals', lang).format(refs=refs, pts=refs))

# /status
@dp.message_handler(commands=['status'])
async def status(msg: types.Message):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        purchases = await conn.fetchval("SELECT COUNT(*) FROM invoices WHERE status='paid' AND created_at::date = CURRENT_DATE")
        pending = await conn.fetchval("SELECT COUNT(*) FROM invoices WHERE status='pending'")
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('status', lang).format(users=users, cards=cards, purchases=purchases, pending=pending, events=0))

async def main():
    await create_pool()
    load_lang()
    logging.info("✅ Bot started")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())

, address):
        return False
    return True

def t(key, lang):
    return LANG.get(lang, LANG['en']).get(key, LANG['en'].get(key, key))

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

# /start
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for code, label in [('he','🇮🇱 עברית'),('en','🇬🇧 English'),('ru','🇷🇺 Русский'),
                        ('ar','🇸🇦 العربية'),('fr','🇫🇷 Français'),('es','🇪🇸 Español'),
                        ('zh','🇨🇳 中文'),('pt','🇧🇷 Português')]:
        keyboard.insert(InlineKeyboardButton(label, callback_data=f"lang_{code}"))
    await msg.answer(t('choose_lang', 'en'), reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split('_')[1]
    async with pool.acquire() as conn:
        await conn.execute("""INSERT INTO users (user_id, lang) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET lang=$2""", call.from_user.id, lang)
    await call.message.edit_text(t('welcome', lang))
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(t('create_card', lang), t('my_card', lang))
    kb.add(t('premium', lang), t('earnings', lang))
    kb.add(t('leaderboard', lang), t('help', lang))
    await call.message.answer(t('help_text', lang), reply_markup=kb)
    await call.answer()


@dp.message_handler(commands=['connect'])
async def connect_wallet(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=# /language', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    guide = (
        "🔗 <b>Connect Your TON Wallet</b>\n\n"
        "1. Open <a href='https://tonkeeper.com/'>Tonkeeper</a> or <a href='https://wallet.ton.org/'>TON Wallet</a>\n"
        "2. Copy your wallet address (starts with UQ...)\n"
        "3. Send it here: /wallet YOUR_ADDRESS\n\n"
        "Example: /wallet UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
    )
    await msg.answer(guide, parse_mode='HTML', disable_web_page_preview=True)

# /language
@dp.message_handler(commands=['language'])
async def change_lang(msg: types.Message):
    await start(msg)

# /testsuite (admin)
@dp.message_handler(commands=['testsuite'])
async def test_suite(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    required_keys = ['welcome','choose_lang','create_card','my_card','premium','earnings','leaderboard','help',
                     'card_name','card_prof','card_wallet','card_done','my_card_info','no_card',
                     'setprice_prompt','setprice_done','market','salesboard','guide',
                     'feedback_sent','help_text','leaderboard_empty','leaderboard_msg',
                     'myreferrals','no_referrals','my_earnings','status','ref_earned',
                     'setprice_invalid','market_empty']
    report = "🔍 <b>Translation Audit</b>\n━━━━━━━━━━━━━\n"
    all_ok = True
    for lang in LANG:
        missing = [k for k in required_keys if k not in LANG[lang]]
        if missing:
            report += f"❌ {lang}: missing {', '.join(missing)}\n"
            all_ok = False
    if all_ok:
        report += "✅ All 8 languages have all required keys!\n"
    await msg.answer(report, parse_mode='HTML')

# /commands (admin)
@dp.message_handler(commands=['commands'])
async def list_commands(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    text = """🔧 <b>All Bot Commands</b>
━━━━━━━━━━━━━━━
/start  Choose language
/language  Change language
/testsuite  Translation audit
/claim  Claim free card
/simulate_purchase  Test platform fee
/setprice  Set your price
/market  Price marketplace
/salesboard  Sales leaderboard
/guide  How to earn
/myreferrals  Your referrals
/status  Bot statistics
/feedback  Send feedback
━━━━━━━━━━━━━━━
<b>Card Creation</b>
Use keyboard button to start.
━━━━━━━━━━━━━━━
<b>Admin</b>
/commands  This list
/verify invoice_id  Verify payment
"""
    await msg.answer(text, parse_mode='HTML')

# /claim NIFTI200
@dp.message_handler(commands=['claim'])
async def claim_free_card(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    args = msg.get_args().split()
    if not args or args[0].upper() != "NIFTI200":
        await msg.answer("Invalid promo code. Use /claim NIFTI200")
        return
    async with pool.acquire() as conn:
        async with conn.transaction():
            max_cards = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_max' FOR UPDATE"))
            claimed = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_claimed' FOR UPDATE"))
            if claimed >= max_cards:
                await msg.answer("All free cards claimed! Create a paid card now.")
                return
            already = await conn.fetchval("SELECT COUNT(*) FROM promo_claims WHERE user_id=$1", msg.from_user.id)
            if already:
                await msg.answer("You already claimed a free card.")
                return
            await conn.execute("UPDATE settings SET value = CAST(CAST(value AS int) + 1 AS text) WHERE key='free_cards_claimed'")
            await conn.execute("INSERT INTO promo_claims (user_id, wallet) VALUES ($1, 'none')", msg.from_user.id)
            await msg.answer("✅ Free card activated! Start sharing your link.")

# /simulate_purchase (admin)
@dp.message_handler(commands=['simulate_purchase'])
async def simulate_purchase(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ Admin only")
        return
    args = msg.get_args().split()
    if len(args) < 2:
        await msg.answer("Usage: /simulate_purchase <amount> <seller_id>")
        return
    try:
        amount = float(args[0])
        seller_id = int(args[1])
    except:
        await msg.answer("Invalid arguments")
        return
    fee = platform_fee(amount)
    seller_gets = seller_amount(amount)
    report = (f"<b>Simulated Purchase</b>\n"
              f"Amount: {amount} TON\n"
              f"Platform fee (20%): {fee} TON → Admin wallet\n"
              f"Seller receives: {seller_gets} TON")
    await msg.answer(report, parse_mode='HTML')

# --------------- CARD CREATION ---------------
@dp.message_handler(lambda m: m.text in sum([[LANG[l]['create_card']] for l in LANG], []))
async def create_card(msg: types.Message, state: FSMContext):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('card_name', lang))
    await state.set_state(CardForm.waiting_name)
    await state.update_data(lang=lang)

@dp.message_handler(state=CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    data = await state.get_data()
    await msg.answer(t('card_prof', data['lang']))
    await state.set_state(CardForm.waiting_prof)

@dp.message_handler(state=CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    await state.update_data(prof=msg.text)
    data = await state.get_data()
    await msg.answer(t('card_wallet', data['lang']))
    await state.set_state(CardForm.waiting_wallet)

@dp.message_handler(state=CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    wallet = msg.text.strip()
    async with pool.acquire() as conn:
        await conn.execute("""UPDATE users SET card_name=$1, card_prof=$2, wallet=$3 WHERE user_id=$4""",
                           data['name'], data['prof'], wallet, msg.from_user.id)
    link = f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}"
    await msg.answer(t('card_done', lang).format(link=link))
    await state.finish()


@dp.message_handler(commands=['wallet'])
async def set_wallet(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=# /my_card', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    args = msg.get_args().split()
    if not args:
        await msg.answer("Usage: /wallet YOUR_TON_ADDRESS")
        return
    address = args[0].strip()
    if not is_valid_ton_address(address):
        await msg.answer("❌ Invalid TON address. Must start with UQ... or EQ... and be 48 characters.")
        return
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO wallets (user_id, address, verified) VALUES (# /my_card, $2, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET address=$2, connected_at=NOW()
        """, msg.from_user.id, address)
    await msg.answer(f"✅ Wallet connected!\n<code>{address}</code>", parse_mode='HTML')

# /my_card
@dp.message_handler(lambda m: m.text in sum([[LANG[l]['my_card']] for l in LANG], []))
async def my_card(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
        if not u or not u['card_name']:
            await msg.answer(t('no_card', u['lang'] if u else 'en'))
            return
        lang = u['lang']
        info = t('my_card_info', lang).format(name=u['card_name'], prof=u['card_prof'],
                                              wallet=u['wallet'],
                                              link=f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}")
        await msg.answer(info, parse_mode='HTML')

# /setprice
@dp.message_handler(commands=['setprice'])
async def set_price(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang,price FROM users WHERE user_id=$1', msg.from_user.id)
        if not u:
            await msg.answer("Please /start first.")
            return
        lang = u['lang']
        parts = msg.get_args().split()
        if parts:
            try:
                price = float(parts[0])
                await conn.execute('UPDATE users SET price=$1 WHERE user_id=$2', price, msg.from_user.id)
                await msg.answer(t('setprice_done', lang).format(price=price))
            except:
                await msg.answer(t('setprice_invalid', lang))
        else:
            await msg.answer(t('setprice_prompt', lang).format(price=u['price']))

# /market
@dp.message_handler(commands=['market'])
async def market(msg: types.Message):
    async with pool.acquire() as conn:
        sellers = await conn.fetch("SELECT card_name,price FROM users WHERE card_name IS NOT NULL AND price>0 LIMIT 10")
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    rows = "\n".join(f"{s['card_name']}  {s['price']} TON" for s in sellers) if sellers else t('market_empty', lang)
    await msg.answer(t('market', lang).format(sellers=rows))

# /salesboard
@dp.message_handler(commands=['salesboard'])
async def salesboard(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('salesboard', lang).format(earners='...', sellers='...', rising='...'))

# /guide
@dp.message_handler(commands=['guide'])
async def guide(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('guide', lang))

# /feedback
@dp.message_handler(commands=['feedback'])
async def feedback(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('feedback_sent', lang))

# /myreferrals
@dp.message_handler(commands=['myreferrals'])
async def myreferrals(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
        refs = await conn.fetchval("SELECT COUNT(*) FROM users WHERE ref_id=$1", msg.from_user.id)
    await msg.answer(t('myreferrals', lang).format(refs=refs, pts=refs))

# /status
@dp.message_handler(commands=['status'])
async def status(msg: types.Message):
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        purchases = await conn.fetchval("SELECT COUNT(*) FROM invoices WHERE status='paid' AND created_at::date = CURRENT_DATE")
        pending = await conn.fetchval("SELECT COUNT(*) FROM invoices WHERE status='pending'")
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', msg.from_user.id)
        lang = u['lang'] if u else 'en'
    await msg.answer(t('status', lang).format(users=users, cards=cards, purchases=purchases, pending=pending, events=0))

async def main():
    await create_pool()
    load_lang()
    logging.info("✅ Bot started")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())


