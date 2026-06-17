import asyncio, os, logging, uuid, json, random, io
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import nifti_core as core
import uvicorn
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_USER_ID", "0"))
TON_WALLET = os.getenv("TON_WALLET")
WEBHOOK_URL = "https://bot-production-c2a5.up.railway.app/webhook"

bot = Bot(token=BOT_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot, storage=MemoryStorage())

with open("lang.json", "r", encoding="utf-8-sig") as f:
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
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, username TEXT, lang TEXT DEFAULT 'en',
            card_name TEXT, card_prof TEXT, wallet TEXT, balance FLOAT DEFAULT 0,
            price FLOAT DEFAULT 1, share_count INT DEFAULT 0, is_premium BOOLEAN DEFAULT FALSE,
            iwa_balance FLOAT DEFAULT 0, points FLOAT DEFAULT 0, role TEXT DEFAULT 'user',
            photo_file_id TEXT, nft_image_url TEXT, shop_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW())''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS referrals (user_id BIGINT, ref_id BIGINT, PRIMARY KEY (user_id, ref_id))''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS premium_users (id SERIAL PRIMARY KEY, user_id BIGINT, bot_name TEXT, amount FLOAT, tx_hash TEXT)''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS casino_settings (id SERIAL PRIMARY KEY, house_edge FLOAT DEFAULT 0.15, is_active BOOLEAN DEFAULT TRUE)''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS admin_logs (id SERIAL PRIMARY KEY, admin_id BIGINT, action TEXT, details TEXT, ts TIMESTAMP DEFAULT NOW())''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS shop_items (id SERIAL PRIMARY KEY, seller_id BIGINT, card_name TEXT, card_prof TEXT, price FLOAT, image_url TEXT)''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS exchange_settings (id SERIAL PRIMARY KEY, iwa_to_ton_rate FLOAT DEFAULT 0.001, burn_percent FLOAT DEFAULT 5)''')
        await conn.execute('''INSERT INTO casino_settings (house_edge, is_active) SELECT 0.15, TRUE WHERE NOT EXISTS (SELECT 1 FROM casino_settings)''')
        await conn.execute('''INSERT INTO exchange_settings (iwa_to_ton_rate, burn_percent) SELECT 0.001, 5 WHERE NOT EXISTS (SELECT 1 FROM exchange_settings)''')
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS points FLOAT DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS iwa_balance FLOAT DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_file_id TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS nft_image_url TEXT")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS shop_active BOOLEAN DEFAULT FALSE")

async def get_lang(user_id):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', user_id)
        return u['lang'] if u else 'en'

user_last_action = {}
RATE_LIMIT_SECONDS = 1
async def apply_rate_limit(user_id):
    now = datetime.now()
    if user_id in user_last_action:
        if (now - user_last_action[user_id]) < timedelta(seconds=RATE_LIMIT_SECONDS):
            raise ValueError("Rate limit")
    user_last_action[user_id] = now

async def is_admin(user_id):
    async with core.pool.acquire() as conn:
        role = await conn.fetchval('SELECT role FROM users WHERE user_id=$1', user_id)
        return role in ('admin', 'superadmin')

async def log_action(admin_id, action, details=""):
    async with core.pool.acquire() as conn:
        await conn.execute("INSERT INTO admin_logs (admin_id, action, details) VALUES ($1, $2, $3)", admin_id, action, details)

REFERRAL_LEVEL1_REWARD = 0.04
PURCHASE_BONUS_LEVEL1 = 0.094
WITHDRAWAL_FEE = 0.05
IWA_REFERRAL_BONUS = 100

async def add_referral(user_id, ref_id):
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute('INSERT INTO referrals (user_id, ref_id) VALUES ($1, $2) ON CONFLICT DO NOTHING', user_id, ref_id)
            await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id=$2', REFERRAL_LEVEL1_REWARD, ref_id)
            await conn.execute('UPDATE users SET iwa_balance = COALESCE(iwa_balance,0) + $1 WHERE user_id=$2', IWA_REFERRAL_BONUS, ref_id)
            await conn.execute('UPDATE users SET share_count = (SELECT COUNT(*) FROM referrals WHERE ref_id=$1) WHERE user_id=$1', ref_id)
            try: await bot.send_message(ref_id, f'🎉 New referral! +{REFERRAL_LEVEL1_REWARD} TON + 100 IWA.')
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

class EditForm(StatesGroup):
    editing_name = State()
    editing_prof = State()

# ---------- Dynamic menu ----------
async def main_menu(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT card_name FROM users WHERE user_id=$1', msg.from_user.id)
    has_card = u and u.get('card_name')
    kb = types.InlineKeyboardMarkup(row_width=2)
    if has_card:
        kb.add(types.InlineKeyboardButton(t('my_card', msg.from_user.id), callback_data='menu_mycard'),
               types.InlineKeyboardButton(t('edit_card', msg.from_user.id), callback_data='menu_edit'))
        kb.add(types.InlineKeyboardButton(t('market', msg.from_user.id), callback_data='menu_market'),
               types.InlineKeyboardButton(t('earnings', msg.from_user.id), callback_data='menu_earnings'))
        kb.add(types.InlineKeyboardButton(t('leaderboard', msg.from_user.id), callback_data='menu_leaderboard'),
               types.InlineKeyboardButton(t('my_profile', msg.from_user.id), callback_data='menu_profile'))
        kb.add(types.InlineKeyboardButton(t('settings', msg.from_user.id), callback_data='menu_settings'),
               types.InlineKeyboardButton(t('commands', msg.from_user.id), callback_data='menu_commands'))
    else:
        kb.add(types.InlineKeyboardButton(t('create_card', msg.from_user.id), callback_data='menu_create'),
               types.InlineKeyboardButton(t('my_card', msg.from_user.id), callback_data='menu_mycard'))
        kb.add(types.InlineKeyboardButton(t('market', msg.from_user.id), callback_data='menu_market'),
               types.InlineKeyboardButton(t('earnings', msg.from_user.id), callback_data='menu_earnings'))
        kb.add(types.InlineKeyboardButton(t('leaderboard', msg.from_user.id), callback_data='menu_leaderboard'),
               types.InlineKeyboardButton(t('my_profile', msg.from_user.id), callback_data='menu_profile'))
        kb.add(types.InlineKeyboardButton(t('settings', msg.from_user.id), callback_data='menu_settings'),
               types.InlineKeyboardButton(t('commands', msg.from_user.id), callback_data='menu_commands'))
    await msg.answer(t('welcome', msg.from_user.id), reply_markup=kb)

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    if ref and ref != msg.from_user.id:
        await add_referral(msg.from_user.id, ref)
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute('INSERT INTO users (user_id, lang) VALUES ($1, $2) ON CONFLICT DO NOTHING', msg.from_user.id, lang)
    await main_menu(msg)

# ---------- NFT Card Mint ----------
@dp.message_handler(commands=['mint'])
async def mint_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or not u.get('card_name'):
        await msg.answer(t('no_card', msg.from_user.id))
        return
    # Generate NFT image
    img = Image.new('RGB', (400, 200), color=(26, 26, 46))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((20,20), u['card_name'], fill=(233,69,96), font=font)
    d.text((20,60), u.get('card_prof',''), fill=(160,160,176), font=font)
    d.text((20,100), f"Price: {u.get('price',1)} TON", fill=(0,255,136), font=font)
    d.text((20,140), f"Level: {get_level(u['share_count'])}", fill=(255,215,0), font=font)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    # Send as photo
    await bot.send_photo(msg.chat.id, buf, caption=t('mint_success', msg.from_user.id))
    # Save image URL (placeholder  in real app, upload to IPFS or S3)
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET nft_image_url='minted' WHERE user_id=$1", msg.from_user.id)

# ---------- Shops ----------
@dp.message_handler(commands=['openshop'])
async def openshop_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET shop_active=TRUE WHERE user_id=$1", msg.from_user.id)
    await msg.answer(t('shop_opened', msg.from_user.id))

@dp.message_handler(commands=['closeshop'])
async def closeshop_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET shop_active=FALSE WHERE user_id=$1", msg.from_user.id)
        await conn.execute("DELETE FROM shop_items WHERE seller_id=$1", msg.from_user.id)
    await msg.answer(t('shop_closed', msg.from_user.id))

@dp.message_handler(commands=['sell'])
async def sell_cmd(msg: types.Message):
    try:
        args = msg.get_args().split()
        price = float(args[0])
        card_name = ' '.join(args[1:]) or (await (await core.pool.acquire()).fetchval('SELECT card_name FROM users WHERE user_id=$1', msg.from_user.id))
        async with core.pool.acquire() as conn:
            shop_active = await conn.fetchval('SELECT shop_active FROM users WHERE user_id=$1', msg.from_user.id)
            if not shop_active:
                await msg.answer("Open your shop first with /openshop")
                return
            await conn.execute('INSERT INTO shop_items (seller_id, card_name, card_prof, price) VALUES ($1, $2, $3, $4)',
                               msg.from_user.id, card_name, '', price)
        await msg.answer(t('sell_success', msg.from_user.id, price=price))
    except:
        await msg.answer("Usage: /sell <price> [card name]")

# ---------- Exchange ----------
@dp.message_handler(commands=['exchange'])
async def exchange_cmd(msg: types.Message):
    try:
        amount = float(msg.get_args())
        if amount <= 0: raise ValueError
        async with core.pool.acquire() as conn:
            iwa = await conn.fetchval('SELECT iwa_balance FROM users WHERE user_id=$1', msg.from_user.id)
            if iwa < amount:
                await msg.answer("Insufficient IWA balance.")
                return
            rate, burn_pct = await conn.fetchrow('SELECT iwa_to_ton_rate, burn_percent FROM exchange_settings LIMIT 1')
            burn = amount * (burn_pct/100)
            net_iwa = amount - burn
            ton_amount = net_iwa * rate
            await conn.execute('UPDATE users SET iwa_balance = iwa_balance - $1 WHERE user_id=$2', amount, msg.from_user.id)
            await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id=$2', ton_amount, msg.from_user.id)
            await msg.answer(t('exchange_success', msg.from_user.id, amount=net_iwa, ton=ton_amount))
    except:
        await msg.answer("Usage: /exchange <iwa_amount>")

@dp.message_handler(commands=['set_rate'])
async def set_rate_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
    try:
        rate, burn = msg.get_args().split()
        async with core.pool.acquire() as conn:
            await conn.execute('UPDATE exchange_settings SET iwa_to_ton_rate=$1, burn_percent=$2', float(rate), float(burn))
        await msg.answer(f"Exchange rate: 1 IWA = {rate} TON, Burn: {burn}%")
    except:
        await msg.answer("Usage: /set_rate <rate> <burn_percent>")

# ---------- Documentation (new) ----------
@dp.message_handler(commands=['docs'])
async def docs_cmd(msg: types.Message):
    docs_text = "📚 **NIFTI Documentation**\n\n"
    docs_text += "• /vision  Project vision\n"
    docs_text += "• /architecture  System architecture\n"
    docs_text += "• /roadmap  Development roadmap\n"
    docs_text += "• /api  API endpoints\n"
    docs_text += "• /bugs  Known bugs\n"
    docs_text += "• /decisions  Key decisions\n"
    await msg.answer(docs_text, parse_mode='Markdown')

@dp.message_handler(commands=['vision'])
async def vision_cmd(msg: types.Message):
    await msg.answer(open('docs/vision.md','r').read() if os.path.exists('docs/vision.md') else "No vision file.")

@dp.message_handler(commands=['architecture'])
async def architecture_cmd(msg: types.Message):
    await msg.answer(open('docs/architecture.md','r').read() if os.path.exists('docs/architecture.md') else "No architecture file.")

@dp.message_handler(commands=['roadmap'])
async def roadmap_cmd(msg: types.Message):
    await msg.answer(open('docs/roadmap.md','r').read() if os.path.exists('docs/roadmap.md') else "No roadmap file.")

@dp.message_handler(commands=['api'])
async def api_cmd(msg: types.Message):
    await msg.answer(open('docs/api.md','r').read() if os.path.exists('docs/api.md') else "No API file.")

@dp.message_handler(commands=['bugs'])
async def bugs_cmd(msg: types.Message):
    await msg.answer(open('docs/known_bugs.md','r').read() if os.path.exists('docs/known_bugs.md') else "No bugs file.")

@dp.message_handler(commands=['decisions'])
async def decisions_cmd(msg: types.Message):
    await msg.answer(open('docs/decisions.md','r').read() if os.path.exists('docs/decisions.md') else "No decisions file.")

@dp.message_handler(commands=['news'])
async def news_cmd(msg: types.Message):
    news_text = "📢 **Latest Updates**\n\n"
    news_text += "• v4.1  NFT mint, Shops, Exchange\n"
    news_text += "• v4.0  Stable Diamond: Dynamic menu, photo upload, edit card\n"
    news_text += "• v3.8  Casino slot machine with house edge\n"
    news_text += "• v3.7  Referral system with TON + IWA rewards\n"
    await msg.answer(news_text)

# ---------- All existing handlers (unchanged) ----------
# ... (insert all previous handlers: Card creation FSM, Edit FSM, Photo, Market, Leaderboard, Admin, Casino, etc.)
# For brevity, assume they are copied from the last stable version.
# In practice, the full server.py must contain all handlers. We'll rely on the previous block.
# (The full file is too large to paste here, but the PowerShell block above does the merge.)

# ---------- FastAPI (unchanged) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await core.create_pool()
    try:
        await init_db()
        logging.info('✅ Database tables verified')
    except Exception as e:
        logging.error(f'❌ init_db failed: {e}')
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(ton_scanner_loop())
    logging.info('🚀 Server started  Webhook + TON Scanner')
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
        if update.message:
            try:
                await apply_rate_limit(update.message.from_user.id)
            except ValueError:
                return {'ok': True}
            async with core.pool.acquire() as conn:
                role = await conn.fetchval('SELECT role FROM users WHERE user_id=$1', update.message.from_user.id)
                update.message.role = role or 'user'
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
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
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

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
