import asyncio, os, logging, traceback, re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import core

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())
ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '0'))

@dp.errors_handler()
async def global_error_handler(update, exception):
    logging.error(f'?? Unhandled exception: {exception}\n{traceback.format_exc()}')
    if isinstance(update, types.Update) and update.message:
        await update.message.answer('?? ????? ????? ?????. ??? ??? ??? ????? ????.')
    return True

@dp.message_handler(commands=['cancel'], state='*')
async def cancel_cmd(msg: types.Message, state: FSMContext):
    lang = await get_lang(msg.from_user.id)
    await state.finish()
    await msg.answer(core.t('cancel_msg', lang), reply_markup=core.main_menu(lang))

@dp.message_handler(commands=['restart'], state='*')
async def cmd_restart(msg: types.Message, state: FSMContext):
    await state.finish()
    await start(msg)

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    async with core.pool.acquire() as conn:
        if ref and ref != msg.from_user.id:
            await conn.execute("INSERT INTO users (user_id,lang,ref_id) VALUES ($1,'en',$2) ON CONFLICT DO NOTHING", msg.from_user.id, ref)
            await conn.execute('UPDATE users SET share_count=share_count+1 WHERE user_id=$1', ref)
        else:
            await conn.execute("INSERT INTO users (user_id,lang) VALUES ($1,'en') ON CONFLICT DO NOTHING", msg.from_user.id)
    lang = await get_lang(msg.from_user.id)
    kb = InlineKeyboardMarkup(row_width=2)
    for code, label in [('he','???? ?????'),('en','???? English'),('ru','???? ???????'),('ar','???? ???????'),
                        ('fr','???? Français'),('es','???? Español'),('zh','???? ??'),('pt','???? Português')]:
        kb.insert(InlineKeyboardButton(label, callback_data=f'lang_{code}'))
    await msg.answer(core.t('choose_lang', lang), reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split('_')[1]
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET lang=$1 WHERE user_id=$2', lang, call.from_user.id)
    try:
        await call.message.edit_text(core.t('welcome', lang))
    except:
        pass
    await call.message.answer(core.t('help_text', lang), reply_markup=core.main_menu(lang))
    await call.answer()

async def get_lang(user_id):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT lang FROM users WHERE user_id=$1', user_id)
        return u['lang'] if u else 'en'

@dp.message_handler(commands=['language'])
async def change_lang(msg: types.Message):
    await start(msg)

@dp.message_handler(commands=['guide'])
async def guide(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(core.t('mission_story', lang), parse_mode='HTML')

async def settings_logic(msg, lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(core.t('edit_name', lang), callback_data='edit_name'))
    kb.add(InlineKeyboardButton(core.t('edit_prof', lang), callback_data='edit_prof'))
    kb.add(InlineKeyboardButton(core.t('edit_wallet', lang), callback_data='edit_wallet'))
    kb.add(InlineKeyboardButton(core.t('edit_price', lang), callback_data='edit_price'))
    kb.add(InlineKeyboardButton(core.t('change_language', lang), callback_data='change_lang_menu'))
    kb.add(InlineKeyboardButton(core.t('view_stats', lang), callback_data='view_stats'))
    await msg.answer(core.t('settings_title', lang), reply_markup=kb)

@dp.message_handler(commands=['settings'])
async def settings_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await settings_logic(msg, lang)

@dp.callback_query_handler(lambda c: c.data == 'edit_name')
async def edit_name_start(call: types.CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    await call.message.answer(core.t('card_name', lang))
    await core.EditForm.waiting_name.set()
    await call.answer()

@dp.message_handler(state=core.EditForm.waiting_name)
async def process_edit_name(msg: types.Message, state: FSMContext):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_name=$1 WHERE user_id=$2', msg.text, msg.from_user.id)
    await msg.answer(core.t('name_updated', lang))
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'edit_prof')
async def edit_prof_start(call: types.CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    await call.message.answer(core.t('card_prof', lang))
    await core.EditForm.waiting_prof.set()
    await call.answer()

@dp.message_handler(state=core.EditForm.waiting_prof)
async def process_edit_prof(msg: types.Message, state: FSMContext):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_prof=$1 WHERE user_id=$2', msg.text, msg.from_user.id)
    await msg.answer(core.t('prof_updated', lang))
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'edit_wallet')
async def edit_wallet_start(call: types.CallbackQuery, state: FSMContext):
    lang = await get_lang(call.from_user.id)
    await call.message.answer(core.t('card_wallet', lang))
    await core.EditForm.waiting_wallet.set()
    await call.answer()

@dp.message_handler(state=core.EditForm.waiting_wallet)
async def process_edit_wallet(msg: types.Message, state: FSMContext):
    lang = await get_lang(msg.from_user.id)
    if not core.is_valid_ton(msg.text.strip()):
        await msg.answer(core.t('invalid_wallet', lang))
        return
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET wallet=$1 WHERE user_id=$2', msg.text.strip(), msg.from_user.id)
    await msg.answer(core.t('wallet_updated', lang))
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'edit_price')
async def edit_price_start(call: types.CallbackQuery):
    lang = await get_lang(call.from_user.id)
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT price FROM users WHERE user_id=$1', call.from_user.id)
    price = u['price'] if u else 1
    await call.message.answer(core.t('setprice_prompt', lang).format(price=price))
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'change_lang_menu')
async def change_lang_menu(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    for code, label in [('he','???? ?????'),('en','???? English'),('ru','???? ???????'),('ar','???? ???????'),
                        ('fr','???? Français'),('es','???? Español'),('zh','???? ??'),('pt','???? Português')]:
        kb.insert(InlineKeyboardButton(label, callback_data=f'lang_{code}'))
    await call.message.answer(core.t('choose_lang', 'en'), reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'view_stats')
async def view_stats_cb(call: types.CallbackQuery):
    lang = await get_lang(call.from_user.id)
    async with core.pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
        refs = await conn.fetchval('SELECT COUNT(*) FROM users WHERE ref_id=$1 AND card_name IS NOT NULL', call.from_user.id)
    await call.message.answer(core.t('status', lang).format(users=users, cards=cards) + f'\n?? {core.t("myreferrals", lang).format(refs=refs)}')
    await call.answer()

@dp.message_handler(commands=['share'])
async def share_card(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT card_name FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or not u['card_name']:
        await msg.answer(core.t('no_card', lang)); return
    link = f'https://t.me/NFTY_madness_bot?start={msg.from_user.id}'
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton('?? Telegram', url=f'https://t.me/share/url?url={link}'))
    kb.add(InlineKeyboardButton('?? WhatsApp', url=f'https://wa.me/?text={link}'))
    kb.add(InlineKeyboardButton('?? LinkedIn', url=f'https://www.linkedin.com/sharing/share-offsite/?url={link}'))
    kb.add(InlineKeyboardButton('?? Twitter/X', url=f'https://twitter.com/intent/tweet?url={link}'))
    await msg.answer(core.t('share_message', lang).format(link=link), reply_markup=kb)

@dp.message_handler(commands=['setprice'])
async def set_price(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT price FROM users WHERE user_id=$1', msg.from_user.id)
        if not u: await msg.answer('Please /start first.'); return
        parts = msg.get_args().split()
        if parts:
            try:
                price = float(parts[0])
                if price < 0: raise ValueError
                await conn.execute('UPDATE users SET price=$1 WHERE user_id=$2', price, msg.from_user.id)
                await msg.answer(core.t('setprice_done', lang).format(price=price))
            except:
                await msg.answer(core.t('invalid_price', lang))
        else:
            await msg.answer(core.t('setprice_prompt', lang).format(price=u['price']))

@dp.message_handler(commands=['market'])
async def market_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        sellers = await conn.fetch('SELECT card_name, price FROM users WHERE card_name IS NOT NULL AND price > 0 ORDER BY price DESC LIMIT 10')
    if sellers:
        rows = '\n'.join(f'?? {s["card_name"]}  —  {s["price"]} TON' for s in sellers)
        kb = InlineKeyboardMarkup(row_width=1)
        for s in sellers:
            label = core.t('buy_button', lang).format(price=s['price'])
            kb.add(InlineKeyboardButton(label, callback_data=f'buy_{s["card_name"]}_{s["price"]}'))
        await bot.send_message(msg.chat.id, core.t('market', lang).format(sellers=rows), reply_markup=kb)
    else:
        await msg.answer(core.t('market_empty', lang))

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def buy_card(call: types.CallbackQuery):
    parts = call.data.split('_')
    seller = parts[1]
    price = parts[2]
    await call.answer(f'Coming soon: Buy {seller} for {price} TON', show_alert=True)

@dp.message_handler(commands=['salesboard'])
async def salesboard_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        top = await conn.fetch('SELECT card_name, share_count FROM users WHERE card_name IS NOT NULL ORDER BY share_count DESC LIMIT 10')
    if top:
        lines = '\n'.join(f'{i+1}. {r["card_name"]} — {r["share_count"]} shares' for i, r in enumerate(top))
        await msg.answer(f'{core.t("leaderboard_title", lang)}\n\n{lines}')
    else:
        await msg.answer(core.t('market_empty', lang))

@dp.message_handler(commands=['myreferrals'])
async def myreferrals_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT share_count FROM users WHERE user_id=$1', msg.from_user.id)
        refs = await conn.fetchval('SELECT COUNT(*) FROM users WHERE ref_id=$1 AND card_name IS NOT NULL', msg.from_user.id)
    await msg.answer(core.t('myreferrals', lang).format(refs=refs) + f'\n?? Shares: {u["share_count"] if u else 0}')

@dp.message_handler(commands=['status'])
async def status_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        users = await conn.fetchval('SELECT COUNT(*) FROM users')
        cards = await conn.fetchval('SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL')
    await msg.answer(core.t('status', lang).format(users=users, cards=cards))

@dp.message_handler(commands=['feedback'])
async def feedback_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    text = msg.get_args()
    if text and ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, f'?? Feedback from @{msg.from_user.username} ({msg.from_user.id}):\n{text}')
        except: pass
    await msg.answer(core.t('feedback_sent', lang))

async def my_card_logic(msg, lang):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT * FROM users WHERE user_id=$1', msg.from_user.id)
    if not u or not u['card_name']:
        await msg.answer(core.t('no_card', lang)); return
    link = f'https://t.me/NFTY_madness_bot?start={msg.from_user.id}'
    info = core.t('my_card_info', lang).format(name=u['card_name'], prof=u['card_prof'] or '', wallet=u['wallet'] or core.t('no_wallet', lang), link=link)
    await msg.answer(info, parse_mode='HTML')

@dp.message_handler(commands=['my_card'])
async def my_card_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await my_card_logic(msg, lang)

@dp.message_handler(commands=['earnings'])
async def earnings_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow('SELECT balance, price, share_count FROM users WHERE user_id=$1', msg.from_user.id)
    if not u: await msg.answer('Please /start first.'); return
    balance = u['balance'] or 0
    price = u['price'] or 1
    fee = core.platform_fee(float(price))
    net = core.seller_amount(float(price))
    text = core.t('earnings_details', lang).format(
        earnings=core.t('earnings', lang),
        balance=balance, price=price, fee=fee, net=net, shares=u['share_count']
    )
    await msg.answer(text)

@dp.message_handler(commands=['leaderboard'])
async def leaderboard_cmd(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        top = await conn.fetch('SELECT card_name, share_count FROM users WHERE card_name IS NOT NULL ORDER BY share_count DESC LIMIT 10')
    if top:
        lines = '\n'.join(f'{i+1}. {r["card_name"]} — {r["share_count"]} shares' for i, r in enumerate(top))
        await msg.answer(f'{core.t("leaderboard_title", lang)}\n\n{lines}')
    else:
        await msg.answer(core.t('market_empty', lang))

@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer('? Admin only'); return
    text = msg.get_args()
    if not text: await msg.answer('Usage: /broadcast <message>'); return
    async with core.pool.acquire() as conn:
        rows = await conn.fetch('SELECT user_id FROM users')
    sent, failed = 0, 0
    for r in rows:
        try:
            await bot.send_message(r['user_id'], text)
            sent += 1
            await asyncio.sleep(0.05)
        except: failed += 1
    await msg.answer(f'? Broadcast: {sent} sent, {failed} failed')

@dp.message_handler(commands=['minisite'])
async def minisite_cmd(msg: types.Message):
    url = msg.get_args().strip()
    if not url: await msg.answer('Usage: /minisite <url>'); return
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET minisite=$1 WHERE user_id=$2', url, msg.from_user.id)
    await msg.answer(f'? Mini-site set: {url}')

@dp.message_handler(commands=['connect'])
async def connect_wallet(msg: types.Message):
    await msg.answer('?? Connect TON Wallet\n1. Open Tonkeeper\n2. Copy address (UQ... or EQ...)\n3. Send: /wallet YOUR_ADDRESS', disable_web_page_preview=True)

@dp.message_handler(commands=['wallet'])
async def set_wallet(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    args = msg.get_args().split()
    if not args: await msg.answer('Usage: /wallet YOUR_TON_ADDRESS'); return
    addr = args[0].strip()
    if not core.is_valid_ton(addr): await msg.answer(core.t('invalid_wallet', lang)); return
    async with core.pool.acquire() as conn:
        await conn.execute('INSERT INTO wallets (user_id, address, verified) VALUES ($1,$2,FALSE) ON CONFLICT (user_id) DO UPDATE SET address=$2', msg.from_user.id, addr)
        await conn.execute('UPDATE users SET wallet=$1 WHERE user_id=$2', addr, msg.from_user.id)
    await msg.answer(f'? {core.t("wallet_updated", lang)}\n`{addr}`', parse_mode='Markdown')

@dp.message_handler(commands=['testsuite'])
async def test_suite(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer('? Admin only'); return
    required = [
        'welcome','choose_lang','create_card','my_card','premium','earnings','leaderboard','help','settings_menu',
        'card_name','card_prof','card_wallet','card_done','my_card_info','no_card','setprice_prompt','setprice_done',
        'market','market_empty','salesboard','guide','feedback_sent','help_text','myreferrals','status',
        'mission_story','share_message','settings_title','edit_name','edit_prof','edit_wallet','edit_price',
        'change_language','view_stats','level_up','name_updated','prof_updated','wallet_updated','invalid_wallet','cancel_msg',
        'invalid_price','no_wallet','cancelled_due_to_menu','leaderboard_title','earnings_details','buy_button'
    ]
    missing = []
    for lang in core.LANG:
        for key in required:
            if key not in core.LANG[lang]:
                missing.append(f'{lang}:{key}')
    if missing:
        for i in range(0, len(missing), 20):
            await msg.answer('? Missing:\n' + '\n'.join(missing[i:i+20]))
    else:
        await msg.answer('? All languages complete!')

@dp.message_handler(commands=['commands'])
async def list_commands(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer('? Admin only'); return
    await msg.answer('?? All Commands\n/start /language /connect /wallet /setprice /market /salesboard /leaderboard /earnings /myreferrals /status /feedback /cancel /broadcast /minisite /testsuite /commands')

@dp.message_handler(commands=['claim'])
async def claim_free_card(msg: types.Message):
    args = msg.get_args().split()
    if not args or args[0].upper() != 'NIFTI200':
        await msg.answer('Invalid promo code. Use /claim NIFTI200'); return
    async with core.pool.acquire() as conn:
        async with conn.transaction():
            max_cards = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_max' FOR UPDATE"))
            claimed = int(await conn.fetchval("SELECT value FROM settings WHERE key='free_cards_claimed' FOR UPDATE"))
            if claimed >= max_cards: await msg.answer('All free cards claimed!'); return
            already = await conn.fetchval('SELECT COUNT(*) FROM promo_claims WHERE user_id=$1', msg.from_user.id)
            if already: await msg.answer('You already claimed a free card.'); return
            await conn.execute("UPDATE settings SET value = CAST(CAST(value AS int) + 1 AS text) WHERE key='free_cards_claimed'")
            await conn.execute('INSERT INTO promo_claims (user_id, wallet) VALUES ($1, NULL)', msg.from_user.id)
            await msg.answer(f'? Free card activated! ({claimed+1}/{max_cards})')

@dp.message_handler(commands=['simulate_purchase'])
async def simulate_purchase(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: await msg.answer('? Admin only'); return
    args = msg.get_args().split()
    try: amount = float(args[0]) if args else 10.0
    except: amount = 10.0
    fee = core.platform_fee(amount)
    net = core.seller_amount(amount)
    await msg.answer(f'?? Simulation\nAmount: {amount} TON\nFee (20%): {fee} TON\nSeller gets: {net} TON')

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('my_card', l) for l in core.LANG])
async def my_card_btn(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await my_card_logic(msg, lang)

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('premium', l) for l in core.LANG])
async def premium_btn(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(core.t('premium_info', lang))

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('earnings', l) for l in core.LANG])
async def earnings_btn(msg: types.Message):
    await earnings_cmd(msg)

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('leaderboard', l) for l in core.LANG])
async def leaderboard_btn(msg: types.Message):
    await leaderboard_cmd(msg)

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('settings_menu', l) for l in core.LANG])
async def settings_btn(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await settings_logic(msg, lang)

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('help', l) for l in core.LANG])
async def help_btn(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(core.t('help_text', lang))

@dp.message_handler(lambda m: core.LANG and m.text in [core.t('create_card', l) for l in core.LANG])
async def create_card_kb(msg: types.Message, state: FSMContext):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(core.t('card_name', lang))
    await state.set_state(core.CardForm.waiting_name)
    await state.update_data(lang=lang)

async def fsm_guard(msg, state):
    return bool(core.LANG and msg.text in core.all_menu_labels())

@dp.message_handler(state=core.CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    if await fsm_guard(msg, state):
        data = await state.get_data()
        lang = data.get('lang', 'en')
        await state.finish()
        await msg.answer(core.t('cancelled_due_to_menu', lang), reply_markup=core.main_menu(lang))
        return
    await state.update_data(name=msg.text)
    data = await state.get_data()
    await msg.answer(core.t('card_prof', data['lang']))
    await state.set_state(core.CardForm.waiting_prof)

@dp.message_handler(state=core.CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    if await fsm_guard(msg, state):
        data = await state.get_data()
        lang = data.get('lang', 'en')
        await state.finish()
        await msg.answer(core.t('cancelled_due_to_menu', lang), reply_markup=core.main_menu(lang))
        return
    await state.update_data(prof=msg.text)
    data = await state.get_data()
    await msg.answer(core.t('card_wallet', data['lang']))
    await state.set_state(core.CardForm.waiting_wallet)

@dp.message_handler(state=core.CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    if await fsm_guard(msg, state):
        await state.finish()
        await msg.answer(core.t('cancelled_due_to_menu', lang), reply_markup=core.main_menu(lang))
        return
    wallet = msg.text.strip()
    if not core.is_valid_ton(wallet):
        await msg.answer(core.t('invalid_wallet', lang)); return
    async with core.pool.acquire() as conn:
        await conn.execute('UPDATE users SET card_name=$1, card_prof=$2, wallet=$3 WHERE user_id=$4',
                           data['name'], data['prof'], wallet, msg.from_user.id)
    link = f'https://t.me/NFTY_madness_bot?start={msg.from_user.id}'
    await msg.answer(core.t('card_done', lang).format(link=link), reply_markup=core.main_menu(lang))
    await state.finish()

async def on_startup(dp):
    await core.create_pool()
    core.load_lang()
    logging.info('? NIFTI Bot started')

async def on_shutdown(dp):
    logging.info('Shutting down...')
    await dp.storage.close()
    await dp.storage.wait_closed()
    if core.pool:
        await core.pool.close()
    logging.info('? All connections closed.')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
