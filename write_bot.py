# write_bot.py
bot_code = r"""import asyncio, logging, os, random, string, uuid, aiohttp, io, qrcode, csv, tempfile, json
from datetime import datetime, date, timedelta
from decimal import Decimal

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile, ContentType, FSInputFile
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

# ---------- TRANSLATIONS ----------
LANG = {
    "en": {
        "welcome": "👋 Welcome to NIFTI!\n\nYour smart business card awaits.\nCreate your free card now (TON wallet required).",
        "choose_lang": "🌐 Choose language / בחר שפה",
        "create_card": "💳 Create Free Card",
        "my_card": "📇 My Card",
        "premium": "🛍 Premium Products",
        "earnings": "💰 My Earnings",
        "leaderboard": "🏆 Leaderboard",
        "help": "ℹ️ Help",
        "card_name": "📝 Let's start! What name should appear on your card?",
        "card_prof": "💼 What is your profession?",
        "card_wallet": "💎 Please enter your TON wallet address.\nRequired to receive payments.\nSend the address (UQ...)",
        "card_done": "🎉 Your card has been created!\n\nShare your personal link to invite friends and earn 85% commission on their purchases.",
        "my_card_info": "📇 <b>My Card</b>\n\n👤 Name: {name}\n💼 Profession: {prof}\n💎 TON Wallet: <code>{wallet}</code>\n\n🔗 Referral Link:\n<code>{link}</code>\n\nShare this link to invite friends and earn.",
        "no_card": "You haven't created a card yet. Click 'Create Free Card'.",
        "setprice_prompt": "💰 Your current selling price: <b>{price} TON</b>\nUse /setprice <amount> to change it.",
        "setprice_done": "✅ Selling price updated to {price} TON.",
        "market": "🏪 <b>Price Marketplace</b>\n\nBuy from trusted sellers:\n\n{sellers}\nYour price: /setprice",
        "salesboard": "📊 <b>Sales Leaderboard</b>\n\n🏆 Top Earners (30d):\n{earners}\n🔥 Top Sellers (direct sales):\n{sellers}\n🚀 Rising Stars:\n{rising}",
        "guide": "📚 <b>How to Earn with NIFTI</b>\n\n1. Create your free card.\n2. Set your selling price (/setprice).\n3. Share your referral link.\n4. When someone buys through you, you earn 51% of the price!\n5. The more you sell, the higher you rank.\n6. Check /market and /salesboard to see top performers.",
        "feedback_sent": "📨 Feedback sent to admin. Thank you!",
        "admin_only": "⛔ Admin only.",
        "verify_usage": "Usage: /verify invoice_id",
        "invoice_not_found": "❌ Invoice not found.",
        "already_verified": "ℹ️ Already verified.",
        "purchase_verified": "✅ Purchase {invoice_id} verified.",
        "purchase_init": "💳 <b>Purchase</b>\nProduct: {product}\nPrice: {price} TON\n\nSend exactly {price} TON to:\n<code>{wallet}</code>\n\nUnique ID (pass as COMMENT):\n<code>{invoice_id}</code>\n\nPayment will be verified automatically within minutes.",
        "payment_received": "✅ Payment received! Purchase complete.",
        "no_products": "No products available.",
        "buy_btn": "Buy for {price} TON",
        "help_text": "ℹ️ <b>Help</b>\n\n1. Create your free digital card.\n2. Share your referral link.\n3. When a friend buys through you  you earn 85% commission!\n4. Join the weekly referral contest  check 'Leaderboard'.\n\nSupport: @osifungar",
        "leaderboard_empty": "No data yet.",
        "leaderboard_msg": "🏆 <b>Leaderboard  Weekly Contest</b>\n\n{rows}",
        "myreferrals": "📊 Your referrals: {refs} | Points: {pts}",
        "no_referrals": "You have no referrals yet. Share your personal link!",
        "my_earnings": "💰 Your earnings: {total} TON",
        "status": "📊 NIFTI Bot Status\n━━━━━━━━━━━━━━━━━━\n👥 Users: {users}\n🃏 Cards: {cards}\n🛒 Today's purchases: {purchases}\n⏳ Pending verifications: {pending}\n📈 Total events: {events}\n✅ DB connection: OK\n━━━━━━━━━━━━━━━━━━\n🎯 Goal: 1,000 active identities",
        "funnel": "📊 <b>Sales Funnel</b>\n\n👥 Starts: {starts}\n📝 Signups: {signups}\n🃏 Cards created: {cards}\n🛒 Purchases initiated: {purchases}\n💰 Completed payments: {payments}\n\nCard conversion: {card_conv:.1f}%\nPurchase conversion: {purch_conv:.1f}%",
        "coupons_generated": "✅ 100 coupons generated. Example: <code>{code}</code>",
        "coupons_stats": "🎟 <b>Coupons</b>\nTotal: {total}\nUsed: {used}\nActive: {active}",
        "export_done": "📊 Purchases export",
        "admin_panel": "🔧 <b>Admin Panel</b>\n\n/addproduct name | description | price\n/delproduct id\n/toggleproduct id\n/viewpurchases\n/viewcoupons\n/generate_coupons\n/export",
        "product_added": "✅ Product '{name}' added ({price} TON).",
        "product_deleted": "✅ Product {id} deleted.",
        "product_toggled": "✅ Product {id} {status}.",
        "product_list": "<b>🛒 Products</b>\n\n{rows}",
        "recent_purchases": "<b>📋 Recent Purchases</b>\n\n{rows}",
        "debug_info": "🔍 <b>Debug Info</b>\nUser ID: {user_id}\nLanguage: {lang}\nCard: {card}\nPrice: {price}",
        "ref_earned": "🎉 You earned {amount} TON from a referral!",
    },
    "he": {
        "welcome": "👋 ברוך הבא ל-NIFTI!\n\nכרטיס הביקור החכם שלך מחכה.\nצור כרטיס חינם עכשיו (חובה ארנק TON).",
        "choose_lang": "🌐 בחר שפה / Choose language",
        "create_card": "💳 צור כרטיס חינם",
        "my_card": "📇 הכרטיס שלי",
        "premium": "🛍 מוצרי פרימיום",
        "earnings": "💰 ההכנסות שלי",
        "leaderboard": "🏆 דירוג",
        "help": "ℹ️ עזרה",
        "card_name": "📝 נתחיל! איזה שם יופיע בכרטיס?",
        "card_prof": "💼 מה התחום שלך?",
        "card_wallet": "💎 אנא הזן כתובת ארנק TON.\nחובה כדי לקבל תשלומים.\nשלח כתובת (UQ...)",
        "card_done": "🎉 הכרטיס נוצר!\n\nשתף את הקישור האישי כדי להזמין חברים ולהרוויח 85% עמלה על הרכישות שלהם.",
        "my_card_info": "📇 <b>הכרטיס שלי</b>\n\n👤 שם: {name}\n💼 תחום: {prof}\n💎 ארנק TON: <code>{wallet}</code>\n\n🔗 קישור הפצה:\n<code>{link}</code>\n\nשתף את הקישור כדי להזמין חברים ולהרוויח.",
        "no_card": "עדיין לא יצרת כרטיס. לחץ 'צור כרטיס חינם'.",
        "setprice_prompt": "💰 מחיר המכירה שלך כרגע: <b>{price} TON</b>\nהשתמש ב-/setprice <סכום> כדי לשנות.",
        "setprice_done": "✅ מחיר המכירה עודכן ל-{price} TON.",
        "market": "🏪 <b>שוק המחירים</b>\n\nקנה ממוכרים מומלצים:\n\n{sellers}\nהמחיר שלך: /setprice",
        "salesboard": "📊 <b>לוח מובילים מכירות</b>\n\n🏆 מרוויחים מובילים (30 ימים):\n{earners}\n🔥 מוכרים מובילים (מכירות ישירות):\n{sellers}\n🚀 כוכבים עולים:\n{rising}",
        "guide": "📚 <b>איך להרוויח עם NIFTI</b>\n\n1. צור כרטיס חינם.\n2. קבע מחיר מכירה (/setprice).\n3. שתף את קישור ההפצה.\n4. כשמישהו קונה דרכך, אתה מרוויח 51% מהמחיר!\n5. ככל שתמכור יותר, תדורג גבוה יותר.\n6. בדוק /market ו-/salesboard.",
        "feedback_sent": "📨 המשוב נשלח למנהל. תודה!",
        "admin_only": "⛔ מנהל בלבד.",
        "verify_usage": "שימוש: /verify invoice_id",
        "invoice_not_found": "❌ חשבונית לא נמצאה.",
        "already_verified": "ℹ️ כבר אומת.",
        "purchase_verified": "✅ רכישה {invoice_id} אומתה.",
        "purchase_init": "💳 <b>רכישה</b>\nמוצר: {product}\nמחיר: {price} TON\n\nשלח בדיוק {price} TON אל:\n<code>{wallet}</code>\n\nמזהה ייחודי (העבר כ-COMMENT):\n<code>{invoice_id}</code>\n\nהתשלום יאומת אוטומטית תוך דקות.",
        "payment_received": "✅ התשלום התקבל! הרכישה הושלמה.",
        "no_products": "אין מוצרים זמינים.",
        "buy_btn": "קנה ב-{price} TON",
        "help_text": "ℹ️ <b>עזרה</b>\n\n1. צור כרטיס דיגיטלי חינם.\n2. שתף את קישור ההפצה.\n3. כשחבר קונה דרכך  אתה מרוויח 85% עמלה!\n4. הצטרף לתחרות ההפניות השבועית  בדוק 'דירוג'.\n\nתמיכה: @osifungar",
        "leaderboard_empty": "אין נתונים עדיין.",
        "leaderboard_msg": "🏆 <b>לוח מובילים  תחרות שבועית</b>\n\n{rows}",
        "myreferrals": "📊 ההפניות שלך: {refs} | נקודות: {pts}",
        "no_referrals": "אין לך הפניות עדיין. שתף את הקישור האישי!",
        "my_earnings": "💰 ההכנסות שלך: {total} TON",
        "status": "📊 מצב NIFTI\n━━━━━━━━━━━━━━━━━━\n👥 משתמשים: {users}\n🃏 כרטיסים: {cards}\n🛒 רכישות היום: {purchases}\n⏳ ממתינות לאימות: {pending}\n📈 סה''כ אירועים: {events}\n✅ חיבור DB: תקין\n━━━━━━━━━━━━━━━━━━\n🎯 יעד: 1,000 זהויות פעילות",
        "funnel": "📊 <b>משפך מכירות</b>\n\n👥 כניסות: {starts}\n📝 הרשמות: {signups}\n🃏 כרטיסים נוצרו: {cards}\n🛒 רכישות הותחלו: {purchases}\n💰 תשלומים שהושלמו: {payments}\n\nהמרת כרטיסים: {card_conv:.1f}%\nהמרת רכישות: {purch_conv:.1f}%",
        "coupons_generated": "✅ נוצרו 100 קופונים. דוגמה: <code>{code}</code>",
        "coupons_stats": "🎟 <b>קופונים</b>\nסה''כ: {total}\nבשימוש: {used}\nפעילים: {active}",
        "export_done": "📊 ייצוא רכישות",
        "admin_panel": "🔧 <b>פאנל מנהל</b>\n\n/addproduct name | description | price\n/delproduct id\n/toggleproduct id\n/viewpurchases\n/viewcoupons\n/generate_coupons\n/export",
        "product_added": "✅ המוצר '{name}' נוסף ({price} TON).",
        "product_deleted": "✅ מוצר {id} נמחק.",
        "product_toggled": "✅ מוצר {id} {status}.",
        "product_list": "<b>🛒 מוצרים</b>\n\n{rows}",
        "recent_purchases": "<b>📋 רכישות אחרונות</b>\n\n{rows}",
        "debug_info": "🔍 <b>מידע דיבוג</b>\nמזהה משתמש: {user_id}\nשפה: {lang}\nכרטיס: {card}\nמחיר: {price}",
        "ref_earned": "🎉 הרווחת {amount} TON מהפניה!",
    }
}

user_langs = {}
user_prices = {}

def _(user_id, key, **kwargs):
    lang = user_langs.get(user_id, "en")
    texts = LANG.get(lang, LANG["en"])
    text = texts.get(key, LANG["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text

async def log_event(user_id, event, metadata=None):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO events (user_id, event, metadata) VALUES ($1, $2, $3)",
                               user_id, event, json.dumps(metadata or {}))
    except:
        pass

async def ensure_tables():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id BIGINT PRIMARY KEY,
                language TEXT DEFAULT 'en',
                selling_price NUMERIC(12,2) DEFAULT 3.0
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS xp (
                user_id BIGINT PRIMARY KEY,
                xp INT DEFAULT 0,
                badge TEXT DEFAULT ''
            )
        ''')
    print("✅ extra tables ready")

def main_menu_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_(user_id, "create_card"), callback_data="create_card")],
        [InlineKeyboardButton(text=_(user_id, "my_card"), callback_data="my_card")],
        [InlineKeyboardButton(text=_(user_id, "premium"), callback_data="show_products")],
        [InlineKeyboardButton(text=_(user_id, "earnings"), callback_data="my_earnings")],
        [InlineKeyboardButton(text=_(user_id, "leaderboard"), callback_data="leaderboard")],
        [InlineKeyboardButton(text=_(user_id, "help"), callback_data="help")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 View Purchases", callback_data="admin_purchases")],
        [InlineKeyboardButton(text="🎟 View Coupons", callback_data="admin_coupons")],
        [InlineKeyboardButton(text="📊 Export CSV", callback_data="admin_export")],
        [InlineKeyboardButton(text="🛒 Product List", callback_data="admin_products")],
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    if user_id not in user_langs:
        await message.answer(
            LANG["en"]["choose_lang"],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                 InlineKeyboardButton(text="🇮🇱 עברית", callback_data="lang_he")]
            ])
        )
        return
    await proceed_start(message, command)

@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_langs[callback.from_user.id] = lang
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_settings (user_id, language) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET language = $2
        """, callback.from_user.id, lang)
    await callback.message.edit_text(_(callback.from_user.id, "welcome"))
    await proceed_start(callback.message, None)
    await callback.answer()

async def proceed_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    await log_event(user_id, "start")
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
        if not existing:
            ref_code = f"{user_id}{''.join(random.choices(string.ascii_uppercase, k=4))}"
            invited_by = None
            args = command.args if command else None
            if args and args.startswith("ref_"):
                ref_from = args[4:]
                inviter = await conn.fetchrow("SELECT user_id FROM users WHERE ref_code = $1", ref_from)
                if inviter:
                    invited_by = inviter["user_id"]
            await conn.execute("INSERT INTO users (user_id, username, ref_code, invited_by) VALUES ($1, $2, $3, $4)",
                               user_id, username, ref_code, invited_by)
            await log_event(user_id, "signup", {"ref_code": ref_code})
            if invited_by:
                await conn.execute("""
                    INSERT INTO referral_points (user_id, total_referrals, points, last_referral_at)
                    VALUES ($1, 1, 10, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_referrals = referral_points.total_referrals + 1,
                        points = referral_points.points + 10,
                        last_referral_at = NOW()
                """, invited_by)
                await log_event(invited_by, "referral", {"referred": user_id})
    await message.answer(_(user_id, "welcome"), reply_markup=main_menu_keyboard(user_id))

@router.callback_query(F.data == "create_card")
async def process_create_card(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(_(callback.from_user.id, "card_name"))
    await state.set_state("card:name")
    await callback.answer()

@router.message(StateFilter("card:name"))
async def card_name(message: Message, state: FSMContext):
    await state.update_data(display_name=message.text)
    await message.answer(_(message.from_user.id, "card_prof"))
    await state.set_state("card:profession")

@router.message(StateFilter("card:profession"))
async def card_profession(message: Message, state: FSMContext):
    await state.update_data(profession=message.text)
    await message.answer(_(message.from_user.id, "card_wallet"))
    await state.set_state("card:ton_wallet")

@router.message(StateFilter("card:ton_wallet"))
async def card_ton_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()
    if not wallet.startswith("UQ") or len(wallet) < 48:
        await message.answer("⚠️ Invalid wallet address. Try again.")
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
    await log_event(user_id, "card_created")
    await message.answer(_(user_id, "card_done"), reply_markup=main_menu_keyboard(user_id))
    await state.clear()

@router.callback_query(F.data == "my_card")
async def show_my_card(callback: CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        card = await conn.fetchrow("SELECT * FROM cards WHERE user_id = $1", user_id)
        user = await conn.fetchrow("SELECT ref_code FROM users WHERE user_id = $1", user_id)
    if not card:
        await callback.message.answer(_(user_id, "no_card"))
        await callback.answer()
        return
    ref_link = f"https://t.me/NFTY_madness_bot?start=ref_{user['ref_code']}"
    msg = _(user_id, "my_card_info", name=card['display_name'], prof=card['profession'], wallet=card['ton_wallet'], link=ref_link)
    await callback.message.answer(msg)
    await callback.answer()

@router.callback_query(F.data == "show_products")
async def show_products(callback: CallbackQuery):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, price_ton FROM premium_products WHERE active = true")
    if not rows:
        await callback.message.answer(_(callback.from_user.id, "no_products"))
        await callback.answer()
        return
    for row in rows:
        await callback.message.answer(
            f"🛍 <b>{row['name']}</b>\n{row['description']}\n💎 Price: {row['price_ton']} TON",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_(callback.from_user.id, "buy_btn", price=row['price_ton']), callback_data=f"buy_{row['id']}")]
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
            await callback.answer("Product not found.")
            return
        user = await conn.fetchrow("SELECT invited_by FROM users WHERE user_id = $1", user_id)
        referrer = user["invited_by"] if user else None
        invoice_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO purchases (buyer_user_id, product_id, referrer_user_id, amount_ton, invoice_id, status)
            VALUES ($1, $2, $3, $4, $5, 'pending')
        """, user_id, product_id, referrer, product["price_ton"], invoice_id)
    await log_event(user_id, "purchase_initiated", {"product_id": product_id, "invoice_id": invoice_id})

    qr_data = f"ton://transfer/{TON_WALLET}?amount={product['price_ton']}&text={invoice_id}"
    qr_img = qrcode.make(qr_data)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)
    photo = BufferedInputFile(buf.read(), filename='qr.png')

    await callback.message.answer_photo(
        photo=photo,
        caption=_(user_id, "purchase_init", product=product['name'], price=product['price_ton'], wallet=TON_WALLET, invoice_id=invoice_id)
    )
    await callback.answer("Order created ✅")

@router.callback_query(F.data == "help")
async def help_info(callback: CallbackQuery):
    await callback.message.answer(_(callback.from_user.id, "help_text"))
    await callback.answer()

@router.callback_query(F.data == "leaderboard")
async def show_leaderboard(callback: CallbackQuery):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.user_id, u.username, rp.total_referrals, rp.points
            FROM referral_points rp
            JOIN users u ON u.user_id = rp.user_id
            ORDER BY rp.points DESC LIMIT 10
        """)
    if not rows:
        await callback.message.answer(_(callback.from_user.id, "leaderboard_empty"))
    else:
        lines = []
        for i, r in enumerate(rows, 1):
            name = r['username'] if r['username'] else f"User {r['user_id']}"
            lines.append(f"{i}. {name}  {r['total_referrals']} refs ({r['points']} pts)")
        msg = _(callback.from_user.id, "leaderboard_msg", rows="\n".join(lines))
        await callback.message.answer(msg)
    await callback.answer()

@router.message(Command("myreferrals"))
async def my_referrals(message: Message):
    user_id = message.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT total_referrals, points FROM referral_points WHERE user_id = $1", user_id)
    if row:
        await message.answer(_(user_id, "myreferrals", refs=row['total_referrals'], pts=row['points']))
    else:
        await message.answer(_(user_id, "no_referrals"))

@router.callback_query(F.data == "my_earnings")
async def my_earnings(callback: CallbackQuery):
    user_id = callback.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COALESCE(SUM(amount_ton),0) FROM commissions WHERE to_user_id = $1 AND status = 'paid'", user_id)
    await callback.message.answer(_(user_id, "my_earnings", total=total))
    await callback.answer()

@router.message(Command("status"))
async def cmd_status(message: Message):
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        cards = await conn.fetchval("SELECT COUNT(*) FROM cards")
        today = datetime.now().date()
        purchases = await conn.fetchval("SELECT COUNT(*) FROM purchases WHERE created_at::date = $1", today)
        pending = await conn.fetchval("SELECT COUNT(*) FROM purchases WHERE status = 'pending'")
        events = await conn.fetchval("SELECT COUNT(*) FROM events")
    await message.answer(_(message.from_user.id, "status", users=users, cards=cards, purchases=purchases, pending=pending, events=events))

@router.message(Command("funnel"))
async def cmd_funnel(message: Message):
    pool = await get_pool()
    async with pool.acquire() as conn:
        starts = await conn.fetchval("SELECT COUNT(*) FROM events WHERE event = 'start'")
        signups = await conn.fetchval("SELECT COUNT(*) FROM events WHERE event = 'signup'")
        cards = await conn.fetchval("SELECT COUNT(*) FROM events WHERE event = 'card_created'")
        purchases = await conn.fetchval("SELECT COUNT(*) FROM events WHERE event = 'purchase_initiated'")
        payments = await conn.fetchval("SELECT COUNT(*) FROM purchases WHERE status = 'paid'")
    card_conv = cards / signups * 100 if signups else 0
    purch_conv = payments / purchases * 100 if purchases else 0
    msg = _(message.from_user.id, "funnel", starts=starts, signups=signups, cards=cards, purchases=purchases, payments=payments, card_conv=card_conv, purch_conv=purch_conv)
    await message.answer(msg)

# ---- NEW NIFTI 3.0 COMMANDS ----
@router.message(Command("setprice"))
async def set_price(message: Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args
    if not args:
        price = user_prices.get(user_id, 3.0)
        await message.answer(_(user_id, "setprice_prompt", price=price))
        return
    try:
        price = float(args.strip())
    except:
        await message.answer("Invalid price.")
        return
    user_prices[user_id] = price
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_settings (user_id, selling_price) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET selling_price = $2
        """, user_id, price)
    await message.answer(_(user_id, "setprice_done", price=price))

@router.message(Command("market"))
async def market(message: Message):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.username, u.user_id, COALESCE(us.selling_price, 3.0) AS price,
                   (SELECT COUNT(*) FROM purchases WHERE referrer_user_id = u.user_id AND status = 'paid') AS sales
            FROM users u
            LEFT JOIN user_settings us ON u.user_id = us.user_id
            ORDER BY sales DESC LIMIT 10
        """)
    if not rows:
        await message.answer("Marketplace empty.")
        return
    lines = [f"@{r['username'] or r['user_id']} — {r['price']} TON ({r['sales']} sales)" for r in rows]
    await message.answer(_(message.from_user.id, "market", sellers="\n".join(lines)))

@router.message(Command("salesboard"))
async def salesboard(message: Message):
    pool = await get_pool()
    async with pool.acquire() as conn:
        earners = await conn.fetch("""
            SELECT to_user_id, SUM(amount_ton) AS total
            FROM commissions WHERE status = 'paid' AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY to_user_id ORDER BY total DESC LIMIT 5
        """)
        sellers = await conn.fetch("""
            SELECT referrer_user_id, COUNT(*) AS cnt
            FROM purchases WHERE status = 'paid' AND referrer_user_id IS NOT NULL
            GROUP BY referrer_user_id ORDER BY cnt DESC LIMIT 5
        """)
        rising = []
    earner_lines = [f"{i}. User {r['to_user_id']} — {r['total']:.1f} TON" for i, r in enumerate(earners, 1)] or ["None"]
    seller_lines = [f"{i}. User {r['referrer_user_id']} — {r['cnt']} sales" for i, r in enumerate(sellers, 1)] or ["None"]
    await message.answer(_(message.from_user.id, "salesboard", earners="\n".join(earner_lines), sellers="\n".join(seller_lines), rising="\n".join(rising) or "No data"))

@router.message(Command("guide"))
async def guide(message: Message):
    await message.answer(_(message.from_user.id, "guide"))

@router.message(Command("feedback"))
async def feedback(message: Message, command: CommandObject):
    text = command.args
    if not text:
        await message.answer("Usage: /feedback <your message>")
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO events (user_id, event, metadata) VALUES ($1, 'feedback', $2)",
                           message.from_user.id, json.dumps({"text": text}))
    try:
        await bot.send_message(ADMIN_USER_ID, f"📨 Feedback from @{message.from_user.username}:\n{text}")
    except:
        pass
    await message.answer(_(message.from_user.id, "feedback_sent"))

@router.message(Command("mydebug"))
async def mydebug(message: Message):
    user_id = message.from_user.id
    pool = await get_pool()
    async with pool.acquire() as conn:
        card = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM cards WHERE user_id = $1)", user_id)
        lang = user_langs.get(user_id, "en")
        price = user_prices.get(user_id, 3.0)
    await message.answer(_(user_id, "debug_info", user_id=user_id, lang=lang, card="Yes" if card else "No", price=price))

# ---- ADMIN ----
@router.message(Command("generate_coupons"))
async def generate_coupons(message: Message):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    pool = await get_pool()
    async with pool.acquire() as conn:
        codes = [''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(100)]
        for c in codes:
            await conn.execute("INSERT INTO coupons (code) VALUES ($1) ON CONFLICT DO NOTHING", c)
    await message.answer(_(message.from_user.id, "coupons_generated", code=codes[0]))

@router.message(Command("addproduct"))
async def add_product(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    parts = [p.strip() for p in (command.args or "").split("|")]
    if len(parts) < 3: return await message.answer("Usage: /addproduct name | description | price")
    try: price_val = float(parts[2])
    except: return await message.answer("Price must be a number.")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO premium_products (name, description, price_ton) VALUES ($1, $2, $3)", parts[0], parts[1], price_val)
    await message.answer(_(message.from_user.id, "product_added", name=parts[0], price=price_val))

@router.message(Command("delproduct"))
async def del_product(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    try: pid = int((command.args or "").strip())
    except: return await message.answer("Usage: /delproduct id")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM premium_products WHERE id = $1", pid)
    await message.answer(_(message.from_user.id, "product_deleted", id=pid))

@router.message(Command("toggleproduct"))
async def toggle_product(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    try: pid = int((command.args or "").strip())
    except: return await message.answer("Usage: /toggleproduct id")
    pool = await get_pool()
    async with pool.acquire() as conn:
        cur = await conn.fetchval("SELECT active FROM premium_products WHERE id = $1", pid)
        if cur is None: return await message.answer("Product not found.")
        await conn.execute("UPDATE premium_products SET active = $1 WHERE id = $2", not cur, pid)
    await message.answer(_(message.from_user.id, "product_toggled", id=pid, status="activated" if not cur else "deactivated"))

@router.message(Command("viewpurchases"))
async def view_purchases(message: Message):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.id, p.amount_ton, p.status, p.created_at, u.username
            FROM purchases p JOIN users u ON p.buyer_user_id = u.user_id
            ORDER BY p.created_at DESC LIMIT 20
        """)
    lines = [f"🆔 {r['id']} | {r['amount_ton']} TON | {r['status']} | @{r['username']} | {r['created_at'].strftime('%m/%d %H:%M')}" for r in rows]
    await message.answer(_(message.from_user.id, "recent_purchases", rows="\n".join(lines) if lines else "None"))

@router.message(Command("viewcoupons"))
async def view_coupons(message: Message):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM coupons")
        used = await conn.fetchval("SELECT COUNT(*) FROM coupons WHERE used_count > 0")
        active = await conn.fetchval("SELECT COUNT(*) FROM coupons WHERE active = true")
    await message.answer(_(message.from_user.id, "coupons_stats", total=total, used=used, active=active))

@router.message(Command("export"))
async def export_csv(message: Message):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.id, p.amount_ton, p.status, p.created_at, u.username, pr.name
            FROM purchases p JOIN users u ON p.buyer_user_id = u.user_id JOIN premium_products pr ON p.product_id = pr.id
            ORDER BY p.created_at DESC
        """)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID','Amount TON','Status','Date','User','Product'])
        for r in rows:
            writer.writerow([r['id'], r['amount_ton'], r['status'], r['created_at'].isoformat(), r['username'], r['name']])
        filepath = f.name
    await message.answer_document(FSInputFile(filepath, filename='purchases.csv'), caption=_(message.from_user.id, "export_done"))
    os.unlink(filepath)

@router.message(Command("admin"))
async def admin_menu(message: Message):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    await message.answer(_(message.from_user.id, "admin_panel"), reply_markup=admin_keyboard())

@router.callback_query(F.data == "admin_purchases")
async def cb_purchases(callback: CallbackQuery):
    await view_purchases(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_coupons")
async def cb_coupons(callback: CallbackQuery):
    await view_coupons(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_export")
async def cb_export(callback: CallbackQuery):
    await export_csv(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_products")
async def cb_products(callback: CallbackQuery):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price_ton, active FROM premium_products ORDER BY id")
    lines = [f"{r['id']}. {r['name']}  {r['price_ton']} TON {'✅' if r['active'] else '❌'}" for r in rows]
    await callback.message.answer(_(callback.from_user.id, "product_list", rows="\n".join(lines) if lines else "None"))
    await callback.answer()

@router.message(Command("verify"))
async def admin_verify(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_USER_ID: return await message.answer(_(message.from_user.id, "admin_only"))
    invoice_id = (command.args or "").strip()
    if not invoice_id: return await message.answer(_(message.from_user.id, "verify_usage"))
    pool = await get_pool()
    async with pool.acquire() as conn:
        purchase = await conn.fetchrow("SELECT * FROM purchases WHERE invoice_id = $1", invoice_id)
        if not purchase: return await message.answer(_(message.from_user.id, "invoice_not_found"))
        if purchase["status"] == "paid": return await message.answer(_(message.from_user.id, "already_verified"))
        await conn.execute("UPDATE purchases SET status='paid', tx_hash='manual_verify' WHERE invoice_id=$1", invoice_id)
        if purchase["referrer_user_id"]:
            ref_comm = float(purchase["amount_ton"]) * 0.51
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
        await conn.execute("UPDATE purchases SET commission_paid=true WHERE id=$1", purchase["id"])
    await message.answer(_(message.from_user.id, "purchase_verified", invoice_id=invoice_id))

@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message):
    if ADMIN_USER_ID == 0: return
    caption = f"Payment proof from @{message.from_user.username or message.from_user.id}"
    try:
        await bot.send_photo(ADMIN_USER_ID, message.photo[-1].file_id, caption=caption)
        await message.answer("Receipt forwarded to admin for review.")
    except Exception as e:
        logger.error(f"Failed to forward photo: {e}")

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
                            if resp.status != 200: continue
                            data = await resp.json()
                            if not data.get("ok"): continue
                            for tx in data.get("result", []):
                                comment = tx.get("comment", "")
                                value = float(tx.get("value", 0)) / 1e9
                                if comment == p["invoice_id"] and abs(value - float(p["amount_ton"])) < 0.01:
                                    await conn.execute("UPDATE purchases SET status='paid', tx_hash=$1 WHERE id=$2",
                                                       tx["hash"], p["id"])
                                    if p["referrer_user_id"]:
                                        ref_comm = float(p["amount_ton"]) * 0.51
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
                                    await conn.execute("UPDATE purchases SET commission_paid=true WHERE id=$1", p["id"])
                                    await log_event(p["buyer_user_id"], "payment_completed", {"invoice_id": p["invoice_id"]})
                                    try:
                                        await bot.send_message(p["buyer_user_id"], "✅ Payment received! Purchase complete.")
                                    except: pass
        except Exception as e:
            logger.error(f"Verification loop error: {e}")
        await asyncio.sleep(30)

async def main():
    await ensure_tables()
    dp.include_router(router)
    asyncio.create_task(verify_payments_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
"""

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(bot_code)
print('✅ bot.py created')
