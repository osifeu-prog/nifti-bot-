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

# ---------- Middleware (Rate Limit + Role Injection) ----------
from datetime import datetime, timedelta
user_last_action = {}
RATE_LIMIT_SECONDS = 1

async def on_pre_process_message(msg, data):
    user_id = msg.from_user.id
    now = datetime.now()
    if user_id in user_last_action:
        if (now - user_last_action[user_id]) < timedelta(seconds=RATE_LIMIT_SECONDS):
            await msg.answer("⏳ Please wait before sending another command.")
            raise types.CancelHandler()
    user_last_action[user_id] = now
    # Role injection  check and attach role
    async with core.pool.acquire() as conn:
        role = await conn.fetchval('SELECT role FROM users WHERE user_id=$1', user_id)
        data['user_role'] = role or 'user'

dp.middleware.setup(on_pre_process_message)

# ---------- RBAC Helper ----------
async def is_admin(user_id):
    async with core.pool.acquire() as conn:
        role = await conn.fetchval('SELECT role FROM users WHERE user_id=$1', user_id)
        return role in ('admin', 'superadmin')

# ---------- Audit Log ----------
async def log_action(admin_id, action, details=""):
    async with core.pool.acquire() as conn:
        await conn.execute("INSERT INTO admin_logs (admin_id, action, details) VALUES ($1, $2, $3)", admin_id, action, details)

# ---------- Referral Engine (Atomic Transaction) ----------
REFERRAL_LEVEL1_REWARD = 4.0
PURCHASE_BONUS_LEVEL1 = 9.4
WITHDRAWAL_FEE = 0.05

async def add_referral(user_id, ref_id):
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('INSERT INTO referrals (user_id, ref_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', user_id, ref_id)
            await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id=$2', REFERRAL_LEVEL1_REWARD, ref_id)
            await conn.execute('UPDATE users SET share_count = (SELECT COUNT(*) FROM referrals WHERE ref_id=$1) WHERE user_id=$1', ref_id)
            # FOMO notification
            try: await bot.send_message(ref_id, f'🎉 New referral! +{REFERRAL_LEVEL1_REWARD} TON. Total refs: {(await conn.fetchval("SELECT share_count FROM users WHERE user_id=$1", ref_id))}')
            except: pass

# ---------- Gamification ----------
def get_level(shares):
    if shares >= 50: return '💎 Diamond'
    elif shares >= 15: return '🥇 Gold'
    elif shares >= 5: return '🥈 Silver'
    elif shares >= 1: return '🥉 Bronze'
    return '⚪ Newbie'

# ---------- FSM ----------
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

# (Inline callbacks, FSM, my_card, earnings, market, buy_card, leaderboard, referrals, set_price  as before)
# ---------- Withdrawal ----------
@dp.message_handler(commands=['withdraw'])
async def withdraw_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT balance FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or u['balance'] <= 0:
        await msg.answer("❌ No balance to withdraw.")
        return
    amount = u['balance']
    net = amount * (1 - WITHDRAWAL_FEE)
    links = (
        f"💸 **Withdrawal**\nAmount: {net:.2f} TON (Fee: {WITHDRAWAL_FEE*100}%)\n\n"
        "Convert TON to bank:\n"
        "1. [Transak](https://transak.com/)\n"
        "2. [MoonPay](https://www.moonpay.com/)\n"
        "3. [Bybit P2P](https://www.bybit.com/)\n\n"
        "⚠️ Send TON to your wallet first."
    )
    await msg.answer(links, parse_mode='Markdown', disable_web_page_preview=True)
    await log_action(msg.from_user.id, 'withdraw', f"{amount} TON")

# ---------- Admin (RBAC) ----------
@dp.message_handler(commands=['admin'])
async def admin_menu(msg: types.Message):
    if not await is_admin(msg.from_user.id):
        await msg.answer("⛔ Access Denied.")
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👥 Users Stats", callback_data="adm_stats"),
           types.InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"))
    kb.add(types.InlineKeyboardButton("💰 Airdrop", callback_data="adm_airdrop"),
           types.InlineKeyboardButton("🔑 Grant Admin", callback_data="adm_grant"))
    await msg.answer("🛡️ Admin Control", reply_markup=kb)

# (admin callbacks, /broadcast, /stats, /airdrop, /grant_admin  as before, with log_action)

# ---------- FastAPI ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await core.create_pool()
    core.load_lang()
    asyncio.create_task(ton_scanner_loop())
    logging.info('🚀 Server started  Webhook + RBAC + Viral Engine')
    yield
    logging.info('Server shutting down')

app = FastAPI(lifespan=lifespan)

@app.get('/')
async def index():
    return {'status': 'NIFTI API running'}

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return {'ok': True}

@app.get('/admin')
async def admin_page():
    async with core.pool.acquire() as conn:
        users = await conn.fetch('SELECT * FROM users ORDER BY user_id')
    html = '<h1>Admin Panel</h1><table border=\'1\'><tr><th>ID</th><th>Name</th><th>Balance</th><th>Refs</th></tr>'
    for u in users:
        html += f'<tr><td>{u["user_id"]}</td><td>{u.get("card_name","")}</td><td>{u["balance"]}</td><td>{u["share_count"]}</td></tr>'
    html += '</table>'
    return HTMLResponse(html)

@app.get('/card/{user_id}')
async def card_page(user_id: int):
    # (same as before, with Social Proof + Tonkeeper link)
    return HTMLResponse('<h1>Card</h1>')

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
                                        await conn.execute('INSERT INTO premium_users (user_id, bot_name, amount, tx_hash) VALUES ($1, $2, $3)', user_id, 'nifti', value, tx['transaction_id']['hash'])
                                        try: await bot.send_message(user_id, f'🎉 Payment of {value} TON received!')
                                        except: pass
        except Exception as e: logging.error(f'TON Scanner: {e}')
        await asyncio.sleep(30)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
