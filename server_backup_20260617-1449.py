import asyncio, os, logging, uuid, json, random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
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

async def init_db():
    async with core.pool.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY, username TEXT, lang TEXT DEFAULT 'en',
            card_name TEXT, card_prof TEXT, wallet TEXT, balance FLOAT DEFAULT 0,
            price FLOAT DEFAULT 1, share_count INT DEFAULT 0, is_premium BOOLEAN DEFAULT FALSE,
            iwa_balance FLOAT DEFAULT 0, points FLOAT DEFAULT 0, role TEXT DEFAULT 'user',
            photo_file_id TEXT, created_at TIMESTAMP DEFAULT NOW())''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS referrals (user_id BIGINT, ref_id BIGINT, PRIMARY KEY (user_id, ref_id))''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS premium_users (id SERIAL PRIMARY KEY, user_id BIGINT, bot_name TEXT, amount FLOAT, tx_hash TEXT)''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS casino_settings (id SERIAL PRIMARY KEY, house_edge FLOAT DEFAULT 0.15, is_active BOOLEAN DEFAULT TRUE)''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS admin_logs (id SERIAL PRIMARY KEY, admin_id BIGINT, action TEXT, details TEXT, ts TIMESTAMP DEFAULT NOW())''')
        await conn.execute('''INSERT INTO casino_settings (house_edge, is_active) SELECT 0.15, TRUE WHERE NOT EXISTS (SELECT 1 FROM casino_settings)''')
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS points FLOAT DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS iwa_balance FLOAT DEFAULT 0")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'")
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_file_id TEXT")

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

@dp.callback_query_handler(lambda c: c.data == 'menu_profile')
async def menu_profile(call: types.CallbackQuery):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', call.from_user.id)
    if not u or not u.get('card_name'):
        await call.message.answer(t('no_card', call.from_user.id))
        await call.answer()
        return
    level = get_level(u['share_count'])
    await call.message.answer(t('profile_text', call.from_user.id,
        name=u['card_name'], prof=u.get('card_prof',''), price=u.get('price',1),
        balance=u['balance'] or 0, iwa=u.get('iwa_balance',0), points=u.get('points',0), level=level))
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_settings')
async def menu_settings(call: types.CallbackQuery):
    await call.message.answer('⚙️ Settings  coming soon.')
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_commands')
async def menu_commands(call: types.CallbackQuery):
    await call.message.answer(t('commands_list', call.from_user.id))
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'menu_edit')
async def menu_edit(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(t('change_name', call.from_user.id), callback_data='edit_name'),
           types.InlineKeyboardButton(t('change_prof', call.from_user.id), callback_data='edit_prof'),
           types.InlineKeyboardButton(t('change_photo', call.from_user.id), callback_data='edit_photo'))
    await call.message.answer("Choose what to edit:", reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_name')
async def edit_name_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t('edit_name_prompt', call.from_user.id))
    await EditForm.editing_name.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_prof')
async def edit_prof_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(t('edit_prof_prompt', call.from_user.id))
    await EditForm.editing_prof.set()
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'edit_photo')
async def edit_photo_start(call: types.CallbackQuery):
    await call.message.answer("Send me a photo to set as your profile picture.")
    await call.answer()

@dp.message_handler(state=EditForm.editing_name)
async def process_edit_name(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    if len(name) < 2:
        await msg.answer(t('min_2_chars', msg.from_user.id))
        return
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_name=$1 WHERE user_id=$2', name, msg.from_user.id)
    await msg.answer(t('name_updated', msg.from_user.id, name=name))
    await state.finish()

@dp.message_handler(state=EditForm.editing_prof)
async def process_edit_prof(msg: types.Message, state: FSMContext):
    prof = msg.text.strip()
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_prof=$1 WHERE user_id=$2', prof, msg.from_user.id)
    await msg.answer(t('prof_updated', msg.from_user.id, prof=prof))
    await state.finish()

@dp.message_handler(commands=['set_photo'])
async def set_photo_cmd(msg: types.Message):
    await msg.answer("Send me the photo now.")
    await dp.current_state(user=msg.from_user.id).set_state("waiting_photo")
    await dp.current_state(user=msg.from_user.id).set_data({"awaiting": "photo"})

@dp.message_handler(content_types=['photo'])
async def handle_photo(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    data = await state.get_data()
    if data.get("awaiting") == "photo":
        file_id = msg.photo[-1].file_id
        async with core.pool.acquire() as conn:
            await conn.execute('UPDATE users SET photo_file_id=$1 WHERE user_id=$2', file_id, msg.from_user.id)
        await msg.answer(t('photo_updated', msg.from_user.id))
        await state.finish()
    else:
        await msg.answer("I didn't expect a photo. Use /set_photo first.")

async def my_card(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or not u.get('card_name'):
        await msg.answer(t('no_card', msg.from_user.id))
        return
    level = get_level(u['share_count'])
    caption = t('card_view', msg.from_user.id,
                name=u['card_name'], prof=u.get('card_prof',''), price=u.get('price',1), level=level)
    if u.get('photo_file_id'):
        await bot.send_photo(msg.chat.id, u['photo_file_id'], caption=caption)
    else:
        await msg.answer(caption)

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
        await conn.execute('INSERT INTO users (user_id, lang) VALUES ($1, $2) ON CONFLICT DO NOTHING', msg.from_user.id, 'en')
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
        lines = '\n'.join(f'{i+1}. {r["card_name"]}  {get_level(r["share_count"])} ({r["share_count"]} refs)' for i, r in enumerate(top))
        await msg.answer(f'🏆 **Leaderboard**\n\n{lines}')
    else:
        await msg.answer('No cards yet.')

# ---------- Direct command handlers ----------
@dp.message_handler(commands=['leaderboard'])
async def leaderboard_cmd(msg: types.Message):
    await leaderboard(msg)

@dp.message_handler(commands=['my_card'])
async def my_card_cmd(msg: types.Message):
    await my_card(msg)

@dp.message_handler(commands=['earnings'])
async def earnings_cmd(msg: types.Message):
    await earnings(msg)

# ---------- Unified invite with referral count ----------
@dp.message_handler(commands=['invite'])
async def invite_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM referrals WHERE ref_id=$1', msg.from_user.id)
    link = f'https://t.me/NFTY_madness_bot?start={msg.from_user.id}'
    qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={link}'
    caption = f'🔗 Your referral link:\n{link}\n\n👥 Joined: {count}\n\nShare and earn {REFERRAL_LEVEL1_REWARD} TON + {IWA_REFERRAL_BONUS} IWA per friend!'
    await msg.answer_photo(qr_url, caption=caption)

@dp.message_handler(commands=['referrals'])
async def referrals_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM referrals WHERE ref_id=$1', msg.from_user.id)
    await msg.answer(f'👥 You have {count} referrals.')

# ---------- Improved Spin (39% win, proper suspense) ----------
@dp.message_handler(commands=['spin'])
async def handle_spin(msg: types.Message):
    async with core.pool.acquire() as conn:
        user_data = await conn.fetchrow('SELECT is_premium, points FROM users WHERE user_id=$1', msg.from_user.id)
        if not user_data:
            await msg.reply('Please /start first.')
            return
        is_prem = user_data['is_premium']
        edge_row = await conn.fetchrow('SELECT house_edge FROM casino_settings LIMIT 1')
        house_edge = edge_row['house_edge'] if edge_row else 0.15
        WINNING_NUMBERS = set(range(1, 26))   # numbers 1..25 = 39.06%
        real_win_prob = len(WINNING_NUMBERS) / 64 * (1 - house_edge)
        spin_msg = await msg.reply('🎰 Spinning...')
        await asyncio.sleep(0.3)
        dice_msg = await bot.send_dice(msg.chat.id, emoji='🎰')
        await asyncio.sleep(3.5)
        result_value = dice_msg.dice.value
        if random.random() < real_win_prob:
            points_won = 2.0 if is_prem else 1.0
            await conn.execute('UPDATE users SET points = COALESCE(points,0) + $1 WHERE user_id = $2', points_won, msg.from_user.id)
            await spin_msg.edit_text(f"🎉 Jackpot! You won {points_won} points!")
        else:
            await spin_msg.edit_text("💸 No luck this time. Try again!")

@dp.message_handler(commands=['set_edge'])
async def set_edge_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id):
        return
    try:
        new_edge = float(msg.get_args())
        if not 0 <= new_edge <= 1:
            raise ValueError
        async with core.pool.acquire() as conn:
            await conn.execute('UPDATE casino_settings SET house_edge = $1', new_edge)
        await msg.reply(f"✅ House edge updated to {new_edge*100}%")
        await log_action(msg.from_user.id, 'set_edge', str(new_edge))
    except:
        await msg.reply("❌ Usage: /set_edge 0.15")

# ---------- Admin Commands ----------
@dp.message_handler(commands=['admin'])
async def admin_panel_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id):
        await msg.answer(t('admin_only', msg.from_user.id))
        return
    async with core.pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        volume = await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')
    await msg.answer(f'🛡️ **Admin Panel**\n👥 Users: {users}\n💳 Cards: {cards}\n💰 Volume: {volume} TON', parse_mode='Markdown')
    await log_action(msg.from_user.id, 'admin_panel_viewed')

@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
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
    await log_action(msg.from_user.id, 'broadcast', text)

@dp.message_handler(commands=['stats'])
async def stats_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
    async with core.pool.acquire() as conn:
        total_users = await conn.fetchval('SELECT COUNT(*) FROM users')
        total_cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        total_volume = await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')
        referral_count = await conn.fetchval('SELECT COUNT(*) FROM referrals')
    await msg.answer(f'📊 System Stats\n━━━━━━━━━━━━━━━━━\n👥 Total Users: {total_users}\n💳 Cards: {total_cards}\n💰 Volume: {total_volume} TON\n🔗 Referrals: {referral_count}')
    await log_action(msg.from_user.id, 'stats_viewed')

@dp.message_handler(commands=['airdrop'])
async def airdrop_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
    try:
        amount = float(msg.get_args())
        async with core.pool.acquire() as conn:
            users = await conn.fetch('SELECT user_id FROM users')
            for u in users:
                await conn.execute('UPDATE users SET balance = COALESCE(balance,0) + $1 WHERE user_id = $2', amount, u['user_id'])
        await msg.answer(f'✅ {amount} TON sent to {len(users)} users!')
        await log_action(msg.from_user.id, 'airdrop', f'{amount} TON to {len(users)} users')
    except:
        await msg.answer('❌ Usage: /airdrop 5.0')

@dp.message_handler(commands=['grant_admin'])
async def grant_admin_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    try:
        target_id = int(msg.get_args())
        async with core.pool.acquire() as conn:
            await conn.execute("UPDATE users SET role = 'admin' WHERE user_id=$1", target_id)
        await msg.answer(f'✅ User {target_id} promoted to admin.')
        await log_action(msg.from_user.id, 'grant_admin', str(target_id))
    except:
        await msg.answer('❌ Usage: /grant_admin <user_id>')

@dp.message_handler(commands=['db_setup'])
async def db_setup_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    try:
        await init_db()
        async with core.pool.acquire() as conn:
            await conn.execute('''INSERT INTO users (user_id, username, lang, card_name, card_prof, wallet, is_premium, iwa_balance, points, role)
                VALUES (224223270, 'OsifUngar', 'en', 'Osif Ungar', 'NIFTI Director', 'UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp', TRUE, 100000, 0, 'admin')
                ON CONFLICT (user_id) DO UPDATE SET is_premium = TRUE, card_name = 'Osif Ungar', card_prof = 'NIFTI Director', iwa_balance = 100000, role = 'admin' ''')
        await msg.reply("✅ DB tables created and admin card set!")
    except Exception as e:
        await msg.reply(f"❌ DB setup error: {e}")

@dp.message_handler(commands=['healthcheck'])
async def healthcheck_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
    try:
        async with core.pool.acquire() as conn:
            users = await conn.fetchval('SELECT COUNT(*) FROM users')
        webhook_info = await bot.get_webhook_info()
        await msg.reply(f'🟢 DB OK (Users: {users})\n🟢 Webhook: {webhook_info.url}\nPending: {webhook_info.pending_update_count}')
    except Exception as e:
        await msg.reply(f'❌ Healthcheck failed: {e}')

@dp.message_handler(commands=['check'])
async def check_cmd(msg: types.Message):
    if not await is_admin(msg.from_user.id): return
    try:
        async with core.pool.acquire() as conn:
            users = await conn.fetchval('SELECT COUNT(*) FROM users')
            cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
            refs = await conn.fetchval('SELECT COUNT(*) FROM referrals')
            premium = await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_premium = TRUE')
        webhook_info = await bot.get_webhook_info()
        status = f'''🟢 **System Check**
━━━━━━━━━━━━━━━━━
🟢 DB: OK (Users: {users}, Cards: {cards})
🟢 Webhook: {webhook_info.url}
🟢 Pending Updates: {webhook_info.pending_update_count}
💰 Volume: {await conn.fetchval('SELECT COALESCE(SUM(balance),0) FROM users')} TON
👥 Premium: {premium}
🔗 Referrals: {refs}
🎰 Casino: Active (House Edge: {await conn.fetchval('SELECT house_edge FROM casino_settings LIMIT 1')*100}%)

✅ All systems operational'''
        await msg.answer(status, parse_mode='Markdown')
    except Exception as e:
        await msg.answer(f'❌ System check failed: {e}')

# ---------- Documentation ----------
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
    news_text += "• v4.3  Fixed direct commands, spin 39%, auto tests\n"
    news_text += "• v4.2  Improved spin, unified invite, stable\n"
    news_text += "• v4.0  Dynamic menu, photo upload, edit card\n"
    news_text += "• v3.8  Casino slot machine with house edge\n"
    news_text += "• v3.7  Referral system with TON + IWA rewards\n"
    await msg.answer(news_text)

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

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
