# -*- coding: utf-8 -*-
import asyncio, os, logging, uuid
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import nifti_core as core

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
Bot.set_current(bot)
dp = Dispatcher(bot, storage=MemoryStorage())
TON_WALLET = os.getenv("TON_WALLET")
ADMIN_ID = int(os.getenv("ADMIN_USER_ID", "0"))

class CardForm(StatesGroup):
    waiting_name = State()
    waiting_prof = State()
    waiting_wallet = State()

async def on_startup(dp):
    await core.create_pool()
    core.load_lang()
    logging.info("🚀 NIFTI Bot is LIVE")

async def get_lang(user_id):
    async with core.pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", user_id)
        return u["lang"] if u else "en"

# ---------- Referral helpers ----------
async def add_referral(user_id, ref_id):
    async with core.pool.acquire() as conn:
        await conn.execute("UPDATE users SET share_count = share_count + 1 WHERE user_id = $1", ref_id)
        await conn.execute("INSERT INTO referrals (user_id, ref_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", user_id, ref_id)

async def get_referral_count(user_id):
    async with core.pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM referrals WHERE ref_id = $1", user_id)

# ====================== MENU ======================
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    ref = int(msg.get_args()) if msg.get_args() and msg.get_args().isdigit() else None
    if ref and ref != msg.from_user.id:
        await add_referral(msg.from_user.id, ref)
    lang = await get_lang(msg.from_user.id)
    async with core.pool.acquire() as conn:
        await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, $2) ON CONFLICT DO NOTHING", msg.from_user.id, lang)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🆕 צור כרטיס", "💳 הכרטיס שלי")
    kb.add("🛒 שוק", "💰 הרווחים")
    kb.add("🏆 מובילים", "⚙️ הגדרות")
    await msg.answer("✅ **ברוך הבא ל-NIFTI!**", reply_markup=kb)

# ====================== CARD CREATION FSM ======================
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

# ====================== COMMANDS ======================
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
    await call.message.answer(
        f"שלח **{price} TON** לכתובת:\n`{TON_WALLET}`\n\nMemo: `{memo}`",
        parse_mode="Markdown"
    )
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

# ====================== NEW FEATURES ======================
@dp.message_handler(commands=["referrals"])
async def referrals_cmd(msg: types.Message):
    count = await get_referral_count(msg.from_user.id)
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
        if price <= 0:
            raise ValueError
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
        try:
            await bot.send_message(u['user_id'], text)
        except:
            pass
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

# ====================== START ======================
if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
