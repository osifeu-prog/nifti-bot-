import asyncio, os, logging, uuid, json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import nifti_core as core
import uvicorn

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_USER_ID", "0"))
TON_WALLET = os.getenv("TON_WALLET")
WEBHOOK_URL = "https://bot-production-c2a5.up.railway.app/webhook"

bot = Bot(token=BOT_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot, storage=MemoryStorage())

# ---------- Localization ----------
with open("locales.json", "r", encoding="utf-8-sig") as f:
    LOCALES = json.load(f)

def t(key, user_id=None, **kwargs):
    lang = 'en'
    if user_id:
        try: lang = core.LANG.get(str(user_id), 'en')
        except: pass
    text = LOCALES.get(lang, LOCALES['en']).get(key, LOCALES['en'].get(key, key))
    if kwargs:
        try: text = text.format(**kwargs)
        except: pass
    return text

# ---------- Database init ----------
async def init_db():
    async with core.pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                lang TEXT DEFAULT 'en',
                card_name TEXT,
                card_prof TEXT,
                wallet TEXT,
                balance FLOAT DEFAULT 0,
                price FLOAT DEFAULT 1,
                share_count INT DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                iwa_balance FLOAT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                user_id BIGINT,
                ref_id BIGINT,
                PRIMARY KEY (user_id, ref_id)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS premium_users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                bot_name TEXT,
                amount FLOAT,
                tx_hash TEXT
            )
        ''')

async def get_lang(user_id):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', user_id)
        return u['lang'] if u else 'en'

# ---------- Referral Engine ----------
REFERRAL_LEVEL1_REWARD = 0.04
PURCHASE_BONUS_LEVEL1 = 0.094
WITHDRAWAL_FEE = 0.05

async def add_referral(user_id, ref_id):
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('INSERT INTO referrals (user_id, ref_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', user_id, ref_id)
            await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id=$2', REFERRAL_LEVEL1_REWARD, ref_id)
            await conn.execute('UPDATE users SET share_count = (SELECT COUNT(*) FROM referrals WHERE ref_id=$1) WHERE user_id=$1', ref_id)
            try: await bot.send_message(ref_id, f'🎉 New referral! +{REFERRAL_LEVEL1_REWARD} TON.')
            except: pass

def get_level(shares):
    if shares >= 50: return '💎 Diamond'
    elif shares >= 15: return '🥇 Gold'
    elif shares >= 5: return '🥈 Silver'
    elif shares >= 1: return '🥉 Bronze'
    return '⚪ Newbie'

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

# ---------- Handlers ----------
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    if ref and ref != msg.from_user.id:
        await add_referral(msg.from_user.id, ref)
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute('INSERT INTO users (user_id, lang) VALUES ($1, $2) ON CONFLICT DO NOTHING', msg.from_user.id, lang)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(t('create_card', msg.from_user.id), callback_data='menu_create'),
           types.InlineKeyboardButton(t('my_card', msg.from_user.id), callback_data='menu_mycard'))
    kb.add(types.InlineKeyboardButton(t('market', msg.from_user.id), callback_data='menu_market'),
           types.InlineKeyboardButton(t('earnings', msg.from_user.id), callback_data='menu_earnings'))
    kb.add(types.InlineKeyboardButton(t('leaderboard', msg.from_user.id), callback_data='menu_leaderboard'),
           types.InlineKeyboardButton(t('settings', msg.from_user.id), callback_data='menu_settings'))
    await msg.answer(t('welcome', msg.from_user.id), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'menu_create')
async def menu_create(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t('name_prompt', call.from_user.id))
    await CardForm.waiting_name.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_mycard')
async def menu_mycard(call: types.CallbackQuery):
    await my_card(call.message)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_market')
async def menu_market(call: types.CallbackQuery):
    await market(call.message)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_earnings')
async def menu_earnings(call: types.CallbackQuery):
    await earnings(call.message)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_leaderboard')
async def menu_leaderboard(call: types.CallbackQuery):
    await leaderboard(call.message)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_settings')
async def menu_settings(call: types.CallbackQuery):
    await call.message.answer('⚙️ Settings – coming soon.')
    await call.answer()

@dp.message_handler(state=CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    if len(name) < 2:
        await msg.answer(t('min_2_chars', msg.from_user.id))
        return
    await state.update_data(name=name)
    await msg.answer(t('prof_prompt', msg.from_user.id))
    await CardForm.waiting_prof.set()

@dp.message_handler(state=CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    await state.update_data(prof=msg.text.strip())
    await msg.answer(t('wallet_prompt', msg.from_user.id))
    await CardForm.waiting_wallet.set()

@dp.message_handler(state=CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_name=$1, card_prof=$2, wallet=$3, price=1.0 WHERE user_id=$4',
                           data['name'], data['prof'], msg.text.strip(), msg.from_user.id)
    await msg.answer(t('card_created', msg.from_user.id, name=data['name'], prof=data['prof']))
    await state.finish()

@dp.message_handler(commands=['status'])
async def status(msg: types.Message):
    async with core.pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
    await msg.answer(f'📊 Users: {users} | Cards: {cards}')

async def my_card(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or not u.get('card_name'):
        await msg.answer(t('no_card', msg.from_user.id))
        return
    level = get_level(u['share_count'])
    await msg.answer(f'💳 {u["card_name"]}\nProfession: {u.get("card_prof","")}\nPrice: {u.get("price",1)} TON\n🏅 Level: {level}')

async def earnings(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT balance, price FROM users WHERE user_id=$1', msg.from_user.id)
    if not u:
        await msg.answer(t('send_start', msg.from_user.id))
        return
    price = u['price'] or 1
    fee = core.platform_fee(float(price))
    net = core.seller_amount(float(price))
    await msg.answer(t('balance', msg.from_user.id, balance=u['balance'] or 0, price=price, fee=fee, net=net))

async def market(msg: types.Message):
    async with core.pool.acquire() as conn:
        cards = await conn.fetch('SELECT user_id, card_name, price FROM users WHERE card_name IS NOT NULL ORDER BY price ASC LIMIT 10')
    if not cards:
        await msg.answer('No cards yet.')
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c in cards:
        kb.add(types.InlineKeyboardButton(f'{c["card_name"]} - {c["price"]} TON', callback_data=f'buy_{c["user_id"]}_{c["price"]}'))
    await msg.answer('🛒 **Market**', reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def buy_card(call: types.CallbackQuery):
    _, seller_id, price = call.data.split('_')
    memo = f'NIFTI_PAY:{call.from_user.id}_{uuid.uuid4().hex[:8]}'
    await call.message.answer(f'Send **{price} TON** to:\n`{TON_WALLET}`\n\nMemo: `{memo}`', parse_mode='Markdown')
    async with core.pool.acquire() as conn:
        ref = await conn.fetchval('SELECT ref_id FROM referrals WHERE user_id=$1', call.from_user.id)
        if ref:
            await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id=$2', PURCHASE_BONUS_LEVEL1, ref)
            try: await bot.send_message(ref, f'💰 {call.from_user.first_name} made a purchase! You earned {PURCHASE_BONUS_LEVEL1} TON.')
            except: pass
    await call.answer()

async def leaderboard(msg: types.Message):
    async with core.pool.acquire() as conn:
        top = await conn.fetch('SELECT card_name, share_count FROM users WHERE card_name IS NOT NULL ORDER BY share_count DESC LIMIT 10')
    if top:
        lines = '\n'.join(f'{i+1}. {r["card_name"]} – {get_level(r["share_count"])} ({r["share_count"]} refs)' for i, r in enumerate(top))
        await msg.answer(f'🏆 **Leaderboard**\n\n{lines}')
    else:
        await msg.answer('No cards yet.')

@dp.message_handler(commands=['referrals'])
async def referrals_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM referrals WHERE ref_id=$1', msg.from_user.id)
    link = f'https://t.me/NFTY_madness_bot?start={msg.from_user.id}'
    await msg.answer(t('referrals', msg.from_user.id, count=count, link=link), parse_mode='Markdown')

@dp.message_handler(commands=['set_price'])
async def set_price_cmd(msg: types.Message):
    try:
        price = float(msg.get_args())
        if price <= 0: raise ValueError
        async with core.pool.acquire() as conn:
            await conn.execute('UPDATE users SET price=$1 WHERE user_id=$2', price, msg.from_user.id)
        await msg.answer(t('price_updated', msg.from_user.id, price=price))
    except:
        await msg.answer('❌ Usage: /set_price 5.0')

# Admin commands
@dp.message_handler(commands=['admin'])
async def admin_panel_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer(t('admin_only', msg.from_user.id))
        return
    async with core.pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        volume = await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')
    await msg.answer(f'🛡️ **Admin Panel**\n👥 Users: {users}\n💳 Cards: {cards}\n💰 Volume: {volume} TON', parse_mode='Markdown')

@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    text = msg.get_args()
    if not text:
        await msg.answer('Usage: /broadcast <message>')
        return
    async with core.pool.acquire() as conn:
        all_users = await conn.fetch('SELECT user_id FROM users')
    for u in all_users:
        try: await bot.send_message(u['user_id'], text)
        except: pass
    await msg.answer(f'✅ Sent to {len(all_users)} users.')

@dp.message_handler(commands=['stats'])
async def stats_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    async with core.pool.acquire() as conn:
        total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
        total_cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        total_volume = await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')
        referral_count = await conn.fetchval('SELECT COUNT(*) FROM referrals')
    await msg.answer(f'📊 System Stats\n━━━━━━━━━━━━━━━━━\n👥 Total Users: {total_users}\n💳 Cards: {total_cards}\n💰 Volume: {total_volume} TON\n🔗 Referrals: {referral_count}')

@dp.message_handler(commands=['airdrop'])
async def airdrop_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    try:
        amount = float(msg.get_args())
        async with core.pool.acquire() as conn:
            users = await conn.fetch('SELECT user_id FROM users')
            for u in users:
                await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id = $2', amount, u['user_id'])
        await msg.answer(f'✅ {amount} TON sent to {len(users)} users!')
    except:
        await msg.answer('❌ Usage: /airdrop 5.0')

# ---------- TON Scanner ----------
async def ton_scanner_loop():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                url = f'https://toncenter.com/api/v2/getTransactions?address={TON_WALLET}&limit=5'
                async with s.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tx in data.get('result', []):
                            memo = tx.get('comment', '')
                            if memo.startswith('NIFTI_PAY:'):
                                user_id = int(memo.split(':')[1])
                                value = int(tx['in_msg']['value']) / 1e9
                                async with core.pool.acquire() as conn:
                                    exists = await conn.fetchval('SELECT tx_hash FROM premium_users WHERE tx_hash=$1', tx['transaction_id']['hash'])
                                    if not exists:
                                        await conn.execute('UPDATE users SET is_premium = TRUE WHERE user_id = $1', user_id)
                                        await conn.execute('INSERT INTO premium_users (user_id, bot_name, amount, tx_hash) VALUES ($1, $2, $3, $4)', user_id, 'nifti', value, tx['transaction_id']['hash'])
                                        try: await bot.send_message(user_id, f'🎉 Payment of {value} TON received!')
                                        except: pass
        except Exception as e: logging.error(f'TON Scanner: {e}')
        await asyncio.sleep(30)

# ---------- FastAPI ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await core.create_pool()
    await init_db()                       # <--- יוצר טבלאות אוטומטית
    await bot.set_webhook(WEBHOOK_URL)   # <--- רושם webhook
    asyncio.create_task(ton_scanner_loop())
    logging.info('🚀 Server started – Webhook + TON Scanner')
    yield
    logging.info('Server shutting down')

app = FastAPI(lifespan=lifespan)

@app.get('/')
async def index():
    return {'status': 'NIFTI API running'}

@app.post('/webhook')
async def webhook(request: Request):
    Bot.set_current(bot)
    Dispatcher.set_current(dp)
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.process_update(update)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return {'ok': True}
@app.get('/admin')
async def admin_page():
    async with core.pool.acquire() as conn:
        users = await conn.fetch('SELECT * FROM users ORDER BY user_id')
    html = '<h1>Admin Panel</h1><table border="1"><tr><th>ID</th><th>Name</th><th>Balance</th><th>Refs</th></tr>'
    for u in users:
        html += f'<tr><td>{u["user_id"]}</td><td>{u.get("card_name","")}</td><td>{u["balance"]}</td><td>{u["share_count"]}</td></tr>'
    html += '</table>'
    return HTMLResponse(html)

@app.get('/card/{user_id}')
async def card_page(user_id: int):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', user_id)
    if not u: return HTMLResponse('<h1>Not found</h1>', status_code=404)
    level = get_level(u['share_count'])
    price = u.get('price', 1)
    amount_nano = int(float(price) * 1e9)
    refs = u['share_count']
    iwa = u.get('iwa_balance', 0)
    html = f'''
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{u['card_name']} - NIFTI</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: white; text-align: center; padding: 20px; }}
        .card {{ background: rgba(255,255,255,0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 40px; max-width: 400px; margin: 50px auto; }}
        .name {{ font-size: 2em; font-weight: bold; background: linear-gradient(45deg, #e94560, #ff6b81); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .prof {{ font-size: 1.2em; color: #a0a0b0; }}
        .price {{ font-size: 1.5em; color: #00ff88; margin: 20px 0; }}
        .level {{ color: gold; }}
        .refs {{ color: #ffaa00; }}
        .iwa {{ font-size: 2em; background: linear-gradient(45deg, #00d2ff, #9d50bb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} 100% {{ transform: scale(1); }} }}
        .btn {{ background: #e94560; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-size: 1.1em; margin: 10px; cursor: pointer; }}
    </style></head><body>
    <div class="card">
        <div class="name">{u['card_name']}</div>
        <div class="prof">{u.get('card_prof', '')}</div>
        <div class="level">{level}</div>
        <div class="iwa">💎 {iwa} IWA</div>
        <div class="refs">👥 {refs} referrals</div>
        <div class="price">{price} TON</div>
        <button class="btn" onclick="window.open('https://app.tonkeeper.com/transfer/{TON_WALLET}?amount={amount_nano}&text=NIFTI_PAY:{user_id}', '_blank')">💳 Pay with TON</button>
        <button class="btn" onclick="window.open('https://t.me/share/url?url=https://t.me/NFTY_madness_bot?start={user_id}', '_blank')">🚀 Share & Earn 100 IWA</button>
    </div></body></html>'''
    return HTMLResponse(html)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)