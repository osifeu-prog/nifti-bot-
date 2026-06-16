import asyncio, os, logging, uuid
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

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

async def get_lang(user_id):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", user_id)
        return u["lang"] if u else "en"


# ====================== VIRAL REFERRALS (with Ledger) ======================
REFERRAL_REWARD = 10.0  # TON reward for referrer (adjustable via /set_referral_reward)

@dp.message_handler(commands=["set_referral_reward"])
async def set_referral_reward_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    try:
        global REFERRAL_REWARD
        REFERRAL_REWARD = float(msg.get_args())
        await msg.answer(f"✅ Referral reward set to {REFERRAL_REWARD} TON")
    except:
        await msg.answer("❌ Usage: /set_referral_reward 15.0")

# Modify start handler to credit rewards
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    if ref and ref != msg.from_user.id:
        async with core.pool.acquire() as conn:
            await conn.execute("UPDATE users SET share_count = share_count + 1 WHERE user_id = # ====================== HANDLERS ======================", ref)
            await conn.execute("INSERT INTO referrals (user_id, ref_id) VALUES (# ====================== HANDLERS ======================, $2) ON CONFLICT DO NOTHING", msg.from_user.id, ref)
            # Credit referrer with reward
            await conn.execute("UPDATE users SET balance = COALESCE(balance,0) + # ====================== HANDLERS ====================== WHERE user_id = $2", REFERRAL_REWARD, ref)
            await conn.execute("UPDATE users SET balance = COALESCE(balance,0) + # ====================== HANDLERS ====================== WHERE user_id = $2", REFERRAL_REWARD/2, msg.from_user.id)  # bonus for new user
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute("INSERT INTO users (user_id, lang) VALUES (# ====================== HANDLERS ======================, $2) ON CONFLICT DO NOTHING", msg.from_user.id, lang)
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🆕 צור כרטיס", callback_data="menu_create"), types.InlineKeyboardButton("💳 הכרטיס שלי", callback_data="menu_mycard"))
    kb.add(types.InlineKeyboardButton("🛒 שוק", callback_data="menu_market"), types.InlineKeyboardButton("💰 הרווחים", callback_data="menu_earnings"))
    kb.add(types.InlineKeyboardButton("🏆 מובילים", callback_data="menu_leaderboard"), types.InlineKeyboardButton("⚙️ הגדרות", callback_data="menu_settings"))
    await msg.answer("✅ **ברוך הבא ל-NIFTI!**", reply_markup=kb)

@dp.message_handler(commands=["top_referrers"])
async def top_referrers_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        top = await conn.fetch("SELECT user_id, share_count FROM users WHERE share_count > 0 ORDER BY share_count DESC LIMIT 10")
    if top:
        lines = "\n".join(f"{i+1}. ID {r['user_id']}  {r['share_count']} הפניות" for i, r in enumerate(top))
        await msg.answer(f"🏆 **Top Referrers**\n\n{lines}")
    else:
        await msg.answer("אין עדיין הפניות.")


@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    if ref and ref != msg.from_user.id:
        async with core.pool.acquire() as conn:
            await conn.execute("UPDATE users SET share_count = share_count + 1 WHERE user_id = $1", ref)
            await conn.execute("INSERT INTO referrals (user_id, ref_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", msg.from_user.id, ref)
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, $2) ON CONFLICT DO NOTHING", msg.from_user.id, lang)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🆕 צור כרטיס", "💳 הכרטיס שלי")
    kb.add("🛒 שוק", "💰 הרווחים")
    kb.add("🏆 מובילים", "⚙️ הגדרות")
    await msg.answer("✅ **ברוך הבא ל-NIFTI!**", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "🆕 צור כרטיס")
async def create_card_start(msg: types.Message, state: FSMContext):
    await msg.answer("שם (לפחות 2 תווים):")
    await CardForm.waiting_name.set()

@dp.message_handler(state=CardForm.waiting_name)
async def process_name(msg: types.Message, state: FSMContext):
    name = msg.text.strip()
    if len(name) < 2:
        await msg.answer("❌ מינימום 2 תווים.")
        return
    await state.update_data(name=name)
    await msg.answer("מקצוע:")
    await CardForm.waiting_prof.set()

@dp.message_handler(state=CardForm.waiting_prof)
async def process_prof(msg: types.Message, state: FSMContext):
    await state.update_data(prof=msg.text.strip())
    await msg.answer("ארנק TON:")
    await CardForm.waiting_wallet.set()

@dp.message_handler(state=CardForm.waiting_wallet)
async def process_wallet(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET card_name=$1, card_prof=$2, wallet=$3, price=1.0 WHERE user_id=$4",
                           data['name'], data['prof'], msg.text.strip(), msg.from_user.id)
    await msg.answer(f"🎉 כרטיס נוצר!\nשם: {data['name']}\nמקצוע: {data['prof']}")
    await state.finish()

@dp.message_handler(commands=["status"])
async def status(msg: types.Message):
    async with core.pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
    await msg.answer(f"📊 משתמשים: {users} | כרטיסים: {cards}")

@dp.message_handler(lambda m: m.text in ["💳 הכרטיס שלי", "/my_card"])
async def my_card(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", msg.from_user.id)
    if not u or not u.get("card_name"):
        await msg.answer("אין לך כרטיס. צור חדש.")
        return
    await msg.answer(f"💳 {u['card_name']}\nמקצוע: {u.get('card_prof','')}\nמחיר: {u.get('price',1)} TON")

@dp.message_handler(lambda m: m.text in ["💰 הרווחים", "/earnings"])
async def earnings(msg: types.Message):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow("SELECT balance, price FROM users WHERE user_id=$1", msg.from_user.id)
    if not u:
        await msg.answer("שלח /start")
        return
    price = u["price"] or 1
    fee = core.platform_fee(float(price))
    net = core.seller_amount(float(price))
    await msg.answer(f"💰 יתרה: {u['balance'] or 0} TON\nמחיר: {price} TON\nעמלה: {fee} TON\nאתה מקבל: {net} TON")

@dp.message_handler(lambda m: m.text in ["🛒 שוק", "/market"])
async def market(msg: types.Message):
    async with core.pool.acquire() as conn:
        cards = await conn.fetch("SELECT user_id, card_name, price FROM users WHERE card_name IS NOT NULL ORDER BY price ASC LIMIT 10")
    if not cards:
        await msg.answer("אין כרטיסים.")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    for c in cards:
        kb.add(types.InlineKeyboardButton(f"{c['card_name']} - {c['price']} TON", callback_data=f"buy_{c['user_id']}_{c['price']}"))
    await msg.answer("🛒 **שוק כרטיסים**", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_card(call: types.CallbackQuery):
    _, seller_id, price = call.data.split("_")
    memo = f"NIFTI_PAY:{call.from_user.id}_{uuid.uuid4().hex[:8]}"
    await call.message.answer(f"שלח **{price} TON** לכתובת:\n`{TON_WALLET}`\n\nMemo: `{memo}`", parse_mode="Markdown")
    await call.answer()

@dp.message_handler(commands=["leaderboard"])
async def leaderboard(msg: types.Message):
    async with core.pool.acquire() as conn:
        top = await conn.fetch("SELECT card_name, share_count FROM users WHERE card_name IS NOT NULL ORDER BY share_count DESC LIMIT 10")
    if top:
        lines = "\n".join(f"{i+1}. {r['card_name']} - {r['share_count']} שיתופים" for i, r in enumerate(top))
        await msg.answer(f"🏆 לוח מובילים\n\n{lines}")
    else:
        await msg.answer("אין כרטיסים.")

@dp.message_handler(lambda m: m.text == "⚙️ הגדרות")
async def settings(msg: types.Message):
    await msg.answer("⚙️ הגדרות  בקרוב.")

@dp.message_handler(commands=["referrals"])
async def referrals_cmd(msg: types.Message):
    async with core.pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM referrals WHERE ref_id = $1", msg.from_user.id)
    link = f"https://t.me/NFTY_madness_bot?start={msg.from_user.id}"
    await msg.answer(f"🔗 **הפניות שלך**\n\nנרשמים: {count}\nקישור:\n`{link}`", parse_mode="Markdown")

@dp.message_handler(commands=["edit_card"])
async def edit_card_start(msg: types.Message, state: FSMContext):
    await msg.answer("שם חדש (לפחות 2 תווים):")
    await CardForm.waiting_name.set()

@dp.message_handler(commands=["set_price"])
async def set_price_cmd(msg: types.Message):
    try:
        price = float(msg.get_args())
        if price <= 0: raise ValueError
        async with core.pool.acquire() as conn:
            await conn.execute("UPDATE users SET price = $1 WHERE user_id = $2", price, msg.from_user.id)
        await msg.answer(f"✅ המחיר עודכן ל-{price} TON")
    except:
        await msg.answer("❌ שימוש: /set_price 5.0")

@dp.message_handler(commands=["admin"])
async def admin_panel_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    async with core.pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        volume = await conn.fetchval("SELECT COALESCE(SUM(balance),0) FROM users")
    await msg.answer(f"🛡️ **Admin Panel**\n👥 Users: {users}\n💳 Cards: {cards}\n💰 Volume: {volume} TON", parse_mode="Markdown")

@dp.message_handler(commands=["broadcast"])
async def broadcast_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    text = msg.get_args()
    if not text:
        await msg.answer("שימוש: /broadcast <הודעה>")
        return
    async with core.pool.acquire() as conn:
        all_users = await conn.fetch("SELECT user_id FROM users")
    for u in all_users:
        try: await bot.send_message(u['user_id'], text)
        except: pass
    await msg.answer(f"✅ נשלח ל-{len(all_users)} משתמשים.")

@dp.message_handler(commands=["diagnostics"])
async def diagnostics(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    async with core.pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        volume = await conn.fetchval("SELECT COALESCE(SUM(balance),0) FROM users")
    await msg.answer(f"📊 **Diagnostics**\n👥 Users: {users}\n💳 Cards: {cards}\n💰 Volume: {volume} TON\n🟢 TON Scanner: Active\n📦 Bot v2.0", parse_mode="Markdown")


# ====================== POWER COMMANDS (ADMIN) ======================

@dp.message_handler(commands=["stats"])
async def stats_cmd(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    async with core.pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        today_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at::date = CURRENT_DATE")
        total_cards = await conn.fetchval("SELECT COUNT(*) FROM users WHERE card_name IS NOT NULL")
        total_volume = await conn.fetchval("SELECT COALESCE(SUM(balance),0) FROM users")
        referral_count = await conn.fetchval("SELECT COUNT(*) FROM referrals")
    await msg.answer(
        f"📊 **System Stats**\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {total_users}\n"
        f"🆕 Today: {today_users}\n"
        f"💳 Cards: {total_cards}\n"
        f"💰 Volume: {total_volume} TON\n"
        f"🔗 Referrals: {referral_count}",
        parse_mode="Markdown"
    )

@dp.message_handler(commands=["export_data"])
async def export_data(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("⛔ אדמין בלבד.")
        return
    what = msg.get_args().strip().lower()
    if not what:
        await msg.answer("שימוש: /export_data users|referrals|all")
        return
    async with core.pool.acquire() as conn:
        if what in ("users", "all"):
            users = await conn.fetch("SELECT * FROM users ORDER BY user_id")
            csv = "user_id,username,card_name,card_prof,wallet,balance,price,share_count,is_premium\n"
            for u in users:
                csv += f"{u['user_id']},{u['username']},{u['card_name']},{u['card_prof']},{u['wallet']},{u['balance']},{u['price']},{u['share_count']},{u['is_premium']}\n"
            await msg.answer_document(csv.encode(), caption="users.csv")
        if what in ("referrals", "all"):
            referrals = await conn.fetch("SELECT * FROM referrals ORDER BY user_id")
            csv = "user_id,ref_id\n"
            for r in referrals:
                csv += f"{r['user_id']},{r['ref_id']}\n"
            await msg.answer_document(csv.encode(), caption="referrals.csv")
    await msg.answer("✅ ייצוא הושלם")


async def start_polling():
    try:
        await dp.skip_updates()
        await dp.start_polling()
    except Exception as e:
        logging.error(f"Polling error: {e}")

# ====================== TON Scanner ======================
async def ton_scanner_loop():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as s:
                url = f"https://toncenter.com/api/v2/getTransactions?address={TON_WALLET}&limit=5"
                async with s.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tx in data.get("result", []):
                            memo = tx.get("comment", "")
                            if memo.startswith("NIFTI_PAY:"):
                                user_id = int(memo.split(":")[1])
                                value = int(tx["in_msg"]["value"]) / 1e9
                                tx_hash = tx["transaction_id"]["hash"]
                                async with core.pool.acquire() as conn:
                                    exists = await conn.fetchval("SELECT tx_hash FROM premium_users WHERE tx_hash=$1", tx_hash)
                                    if not exists:
                                        await conn.execute("UPDATE users SET is_premium = TRUE WHERE user_id = $1", user_id)
                                        await conn.execute("INSERT INTO premium_users (user_id, bot_name, amount, tx_hash) VALUES ($1, 'nifti', $2, $3)", user_id, value, tx_hash)
                                        try: await bot.send_message(user_id, f"🎉 Payment of {value} TON received! Premium activated.")
                                        except: pass
        except Exception as e:
            logging.error(f"TON Scanner error: {e}")
        await asyncio.sleep(30)

# ====================== FastAPI ======================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await core.create_pool()
    core.load_lang()
    asyncio.create_task(start_polling())
    asyncio.create_task(ton_scanner_loop())
    logging.info("🚀 Server started  Bot, Admin, TON Scanner")
    yield
    logging.info("Server shutting down")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def index():
    return {"status": "NIFTI API running"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return {"ok": True}

@app.get("/admin")
async def admin_page():
    async with core.pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users ORDER BY user_id")
    html = "<h1>Admin Panel</h1><table border='1'><tr><th>ID</th><th>Name</th><th>Balance</th></tr>"
    for u in users:
        html += f"<tr><td>{u['user_id']}</td><td>{u.get('card_name','')}</td><td>{u['balance']}</td></tr>"
    html += "</table>"
    return HTMLResponse(html)

@app.get("/health")
async def health():
    return {"status": "ok", "db": await core.check_db_health()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)





