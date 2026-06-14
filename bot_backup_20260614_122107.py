import asyncio, logging, os, random, string, uuid, aiohttp
from datetime import datetime, date

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import asyncpg

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")
TON_WALLET = os.getenv("TON_WALLET")
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_pool: asyncpg.Pool = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, server_settings={'client_encoding': 'UTF8'})
        async with _pool.acquire() as conn:
            await conn.execute("SELECT 1")
        logger.info("✅ DB Pool created")
    return _pool

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# ---- Keyboards ----
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 צור כרטיס אישי חינם", callback_data="create_card")],
        [InlineKeyboardButton(text="📇 הכרטיס שלי", callback_data="my_card")],
        [InlineKeyboardButton(text="🛍 מוצרי פרימיום", callback_data="show_products")],
        [InlineKeyboardButton(text="💰 ההכנסות שלי", callback_data="my_earnings")],
        [InlineKeyboardButton(text="🏆 דירוג השבוע", callback_data="leaderboard")],
        [InlineKeyboardButton(text="ℹ️ עזרה", callback_data="help")]
    ])

# ---- Onboarding ----
@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
        if not existing:
            ref_code = f"{user_id}{''.join(random.choices(string.ascii_uppercase, k=4))}"
            invited_by = None
            args = command.args
            if args and args.startswith("ref_"):
                ref_from = args[4:]
                inviter = await conn.fetchrow("SELECT user_id FROM users WHERE ref_code = $1", ref_from)
                if inviter:
                    invited_by = inviter["user_id"]
            await conn.execute("INSERT INTO users (user_id, username, ref_code, invited_by) VALUES ($1, $2, $3, $4)",
                               user_id, username, ref_code, invited_by)
            if invited_by:
                await conn.execute("""
                    INSERT INTO referral_points (user_id, total_referrals, points, last_referral_at)
                    VALUES ($1, 1, 10, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_referrals = referral_points.total_referrals + 1,
                        points = referral_points.points + 10,
                        last_referral_at = NOW()
                """, invited_by)
    await message.answer(
        f"👋 ברוך הבא ל-NIFTI!\n\n"
        f"כרטיס הביקור החכם שלך מחכה לך.\n"
        f"אנא צור את הכרטיס האישי בחינם (חובה להזין ארנק TON).",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "create_card")
async def process_create_card(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 נתחיל! מה השם שיופיע בכרטיס?")
    await state.set_state("card:name")
    await callback.answer()

@router.message(StateFilter("card:name"))
async def card_name(message: Message, state: FSMContext):
    await state.update_data(display_name=message.text)
    await message.answer("💼 מה התחום שלך? (לדוגמה: מעצב גרפי, קבלן, מאמן כושר)")
    await state.set_state("card:profession")

@router.message(StateFilter("card:profession"))
async def card_profession(message: Message, state: FSMContext):
    await state.update_data(profession=message.text)
    await message.answer(
        "💎 אנא הזן את כתובת ארנק ה-TON שלך.\n"
        "חובה על מנת לקבל תשלומים.\n"
        "שלח את הכתובת (UQ...)"
    )
    await state.set_state("card:ton_wallet")

@router.message(StateFilter("card:ton_wallet"))
async def card_ton_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()
    if not wallet.startswith("UQ") or len(wallet) < 48:
        await message.answer("⚠️ כתובת ארנק לא תקינה. נסה שוב.")
        return
    data = await state.get_data()
    user_id = message.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cards (user_id, display_name, profession, ton_wallet)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                profession = EXCLUDED.profession,
                ton_wallet = EXCLUDED.ton_wallet,
                updated_at = NOW()
        """, user_id, data["display_name"], data["profession"], wallet)
    await message.answer(
        "🎉 הכרטיס שלך נוצר בהצלחה!\n\n"
        "השתמש בקישור האישי שלך כדי להזמין חברים ולהרוויח 85% עמלה על רכישותיהם.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()

# ---- My Card ----
@router.callback_query(F.data == "my_card")
async def show_my_card(callback: CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        card = await conn.fetchrow("SELECT * FROM cards WHERE user_id = $1", user_id)
        user = await conn.fetchrow("SELECT ref_code FROM users WHERE user_id = $1", user_id)
    if not card:
        await callback.message.answer("עדיין לא יצרת כרטיס. לחץ על 'צור כרטיס אישי חינם'.")
        await callback.answer()
        return
    ref_link = f"https://t.me/NFTY_madness_bot?start=ref_{user['ref_code']}"
    msg = (
        f"📇 <b>הכרטיס שלי</b>\n\n"
        f"👤 שם: {card['display_name']}\n"
        f"💼 תחום: {card['profession']}\n"
        f"💎 ארנק TON: <code>{card['ton_wallet']}</code>\n\n"
        f"🔗 קישור להפצה:\n"
        f"<code>{ref_link}</code>\n\n"
        f"שתף את הקישור כדי להזמין חברים ולהרוויח."
    )
    await callback.message.answer(msg)
    await callback.answer()

# ---- Products & Purchase ----
@router.callback_query(F.data == "show_products")
async def show_products(callback: CallbackQuery):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, price_ton FROM premium_products WHERE active = true")
    if not rows:
        await callback.message.answer("אין מוצרים זמינים כרגע.")
        await callback.answer()
        return
    for row in rows:
        await callback.message.answer(
            f"🛍 <b>{row['name']}</b>\n"
            f"📝 {row['description']}\n"
            f"💎 מחיר: {row['price_ton']} TON\n"
            f"לחץ לרכישה:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"קנה ב-{row['price_ton']} TON", callback_data=f"buy_{row['id']}")]
            ])
        )
    await callback.answer()

@router.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        product = await conn.fetchrow("SELECT * FROM premium_products WHERE id = $1", product_id)
        if not product:
            await callback.answer("מוצר לא נמצא.")
            return
        user = await conn.fetchrow("SELECT invited_by FROM users WHERE user_id = $1", user_id)
        referrer = user["invited_by"] if user else None
        invoice_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO purchases (buyer_user_id, product_id, referrer_user_id, amount_ton, invoice_id, status)
            VALUES ($1, $2, $3, $4, $5, 'pending')
        """, user_id, product_id, referrer, product["price_ton"], invoice_id)
    await callback.message.answer(
        f"💳 <b>רכישה</b>\n"
        f"מוצר: {product['name']}\n"
        f"מחיר: {product['price_ton']} TON\n\n"
        f"שלח בדיוק {product['price_ton']} TON לכתובת:\n"
        f"<code>{TON_WALLET}</code>\n\n"
        f"מזהה ייחודי (העבר כ-COMMENT):\n"
        f"<code>{invoice_id}</code>\n\n"
        f"התשלום יאומת אוטומטית תוך דקות."
    )
    await callback.answer("הזמנה נוצרה ✅")

# ---- Help ----
@router.callback_query(F.data == "help")
async def help_info(callback: CallbackQuery):
    await callback.message.answer(
        "ℹ️ <b>עזרה</b>\n\n"
        "1. צור כרטיס אישי חינם.\n"
        "2. שתף את הקישור שלך לחברים.\n"
        "3. כשחבר קונה דרכך  אתה מקבל 85% עמלה!\n"
        "4. תחרות שיתופים  כנס ל'דירוג השבוע'.\n\n"
        "לשאלות: @osifungar"
    )
    await callback.answer()

# ---- Leaderboard & Points ----
@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.user_id, u.username, rp.total_referrals, rp.points
            FROM referral_points rp
            JOIN users u ON u.user_id = rp.user_id
            ORDER BY rp.points DESC
            LIMIT 10
        """)
    if not rows:
        await callback.message.answer("אין עדיין נתונים לדירוג.")
    else:
        msg = "🏆 <b>לוח מובילים  תחרות שיתופים</b>\n\n"
        for i, row in enumerate(rows, 1):
            name = row["username"] or f"משתמש {row['user_id']}"
            msg += f"{i}. {name}  {row['total_referrals']} הפניות ({row['points']} נק')\n"
        await callback.message.answer(msg)
    await callback.answer()

@router.message(Command("myreferrals"))
async def my_referrals(message: Message):
    user_id = message.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT total_referrals, points FROM referral_points WHERE user_id = $1", user_id)
        if row:
            await message.answer(f"📊 ההפניות שלך: {row['total_referrals']} | נקודות: {row['points']}")
        else:
            await message.answer("עדיין אין לך הפניות. שתף את הקישור האישי שלך!")

# ---- Earnings ----
@router.callback_query(F.data == "my_earnings")
async def my_earnings(callback: CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COALESCE(SUM(amount_ton),0) FROM commissions WHERE to_user_id = $1 AND status = 'paid'", user_id)
    await callback.message.answer(f"💰 ההכנסות שלך: {total} TON")
    await callback.answer()

# ---- Status ----
@router.message(Command("status"))
async def cmd_status(message: Message):
    pool = await get_pool()
    async with pool.acquire() as conn:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards_count = await conn.fetchval("SELECT COUNT(*) FROM cards")
        today = datetime.now().date()
        purchases_today = await conn.fetchval(
            "SELECT COUNT(*) FROM purchases WHERE created_at::date = $1", today
        )
        pending = await conn.fetchval("SELECT COUNT(*) FROM purchases WHERE status = 'pending'")
    report = (
        "📊 NIFTI Bot Status\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Users: {users_count}\n"
        f"🃏 Cards: {cards_count}\n"
        f"🛒 Today's purchases: {purchases_today}\n"
        f"⏳ Pending verifications: {pending}\n"
        f"✅ DB connection: OK\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Goal: 1,000 active identities"
    )
    await message.answer(report)

# ---- Admin: verify payment manually ----
@router.message(Command("verify"))
async def admin_verify(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("⛔ גישת מנהל בלבד.")
        return
    args = command.args
    if not args:
        await message.answer("שימוש: /verify <invoice_id>")
        return
    invoice_id = args.strip()
    pool = await get_pool()
    async with pool.acquire() as conn:
        purchase = await conn.fetchrow("SELECT * FROM purchases WHERE invoice_id = $1", invoice_id)
        if not purchase:
            await message.answer("❌ מזהה לא נמצא במערכת.")
            return
        if purchase["status"] == "paid":
            await message.answer("ℹ️ רכישה זו כבר אומתה.")
            return
        await conn.execute("UPDATE purchases SET status = 'paid', tx_hash = 'manual_verify' WHERE invoice_id = $1", invoice_id)
        # Distribute commissions
        if purchase["referrer_user_id"]:
            ref_comm = float(purchase["amount_ton"]) * 0.85
            plat_comm = float(purchase["amount_ton"]) * 0.15
            await conn.execute("""
                INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                VALUES ($1, $2, $3, 1, 'paid', $4)
            """, purchase["buyer_user_id"], purchase["referrer_user_id"], ref_comm, purchase["id"])
            await conn.execute("""
                INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                VALUES ($1, $2, $3, 1, 'paid', $4)
            """, purchase["buyer_user_id"], ADMIN_USER_ID, plat_comm, purchase["id"])
        else:
            await conn.execute("""
                INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                VALUES ($1, $2, $3, 1, 'paid', $4)
            """, purchase["buyer_user_id"], ADMIN_USER_ID, float(purchase["amount_ton"]), purchase["id"])
        await conn.execute("UPDATE purchases SET commission_paid = true WHERE id = $1", purchase["id"])
    await message.answer(f"✅ רכישה {invoice_id} אומתה ידנית.")

# ---- TON Payment Verification ----
async def verify_payments_loop():
    await asyncio.sleep(5)
    while True:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                pending = await conn.fetch("SELECT * FROM purchases WHERE status = 'pending'")
                for p in pending:
                    url = f"https://toncenter.com/api/v2/getTransactions?address={TON_WALLET}&limit=5&api_key={TONCENTER_API_KEY}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json()
                            if not data.get("ok"):
                                continue
                            txs = data.get("result", [])
                            for tx in txs:
                                comment = tx.get("comment", "")
                                value = float(tx.get("value", 0)) / 1e9
                                if comment == p["invoice_id"] and abs(value - float(p["amount_ton"])) < 0.01:
                                    await conn.execute("UPDATE purchases SET status = 'paid', tx_hash = $1 WHERE id = $2",
                                                       tx["hash"], p["id"])
                                    if p["referrer_user_id"]:
                                        ref_comm = float(p["amount_ton"]) * 0.85
                                        plat_comm = float(p["amount_ton"]) * 0.15
                                        await conn.execute("""
                                            INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                                            VALUES ($1, $2, $3, 1, 'paid', $4)
                                        """, p["buyer_user_id"], p["referrer_user_id"], ref_comm, p["id"])
                                        await conn.execute("""
                                            INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                                            VALUES ($1, $2, $3, 1, 'paid', $4)
                                        """, p["buyer_user_id"], ADMIN_USER_ID, plat_comm, p["id"])
                                    else:
                                        await conn.execute("""
                                            INSERT INTO commissions (from_user_id, to_user_id, amount_ton, level, status, purchase_id)
                                            VALUES ($1, $2, $3, 1, 'paid', $4)
                                        """, p["buyer_user_id"], ADMIN_USER_ID, float(p["amount_ton"]), p["id"])
                                    await conn.execute("UPDATE purchases SET commission_paid = true WHERE id = $1", p["id"])
                                    try:
                                        await bot.send_message(p["buyer_user_id"], "✅ התשלום התקבל! הרכישה הושלמה.")
                                    except:
                                        pass
        except Exception as e:
            logger.error(f"Verification loop error: {e}")
        await asyncio.sleep(30)

# ---- Main ----
async def main():
    dp.include_router(router)
    asyncio.create_task(verify_payments_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
