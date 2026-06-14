import re
import json

# --- read bot.py ---
with open('bot.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. וודא שה-regex ב-is_valid_ton נקי
code = code.replace(r'^[UE]Q[A-Za-z0-9_-]{46}\$', r'^[UE]Q[A-Za-z0-9_-]{46}$')

# 2. הוספת פונקציית get_lang (אם לא קיימת)
if 'async def get_lang' not in code:
    get_lang_func = '''
async def get_lang(user_id):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", user_id)
        return u["lang"] if u else "en"
'''
    # מכניסים אחרי הפונקציה my_card_cmd (או לפני main)
    insert_point = code.find('async def main():')
    if insert_point == -1:
        insert_point = code.find('if __name__')
    code = code[:insert_point] + get_lang_func + '\n' + code[insert_point:]

# 3. רשימת כל תוויות התפריט (לסינון FSM)
menu_keys = ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"]
menu_labels_code = '''
# Auto-generated menu labels
MENU_LABELS = set()
for lang in LANG:
    for key in ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"]:
        MENU_LABELS.add(LANG[lang].get(key, ""))
'''
# מכניסים אחרי load_lang
if 'MENU_LABELS' not in code:
    code = code.replace('def load_lang():', 'def load_lang():\n    global MENU_LABELS\n    ' + menu_keys.__str__() + '  # placeholder\n')  # not needed, simpler: just insert the block after load_lang
    # Insert after load_lang function
    load_lang_end = code.find('async def create_pool():')
    if load_lang_end == -1:
        load_lang_end = code.find('# ==========')
    code = code[:load_lang_end] + menu_labels_code + '\n' + code[load_lang_end:]

# 4. הוספת handlers לכפתורי התפריט
new_handlers = '''

# ---------- Menu Button Handlers (auto) ----------
@dp.message_handler(lambda m: m.text in [t("my_card", l) for l in LANG])
async def my_card_menu(msg: types.Message):
    await my_card_cmd(msg)

@dp.message_handler(lambda m: m.text in [t("premium", l) for l in LANG])
async def premium_menu(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(t("premium_info", lang))

@dp.message_handler(lambda m: m.text in [t("earnings", l) for l in LANG])
async def earnings_menu(msg: types.Message):
    await myreferrals_cmd(msg)

@dp.message_handler(lambda m: m.text in [t("leaderboard", l) for l in LANG])
async def leaderboard_menu(msg: types.Message):
    await myreferrals_cmd(msg)  # replace with real leaderboard later

@dp.message_handler(lambda m: m.text in [t("settings_menu", l) for l in LANG])
async def settings_menu_btn(msg: types.Message):
    await settings_cmd(msg)

@dp.message_handler(lambda m: m.text in [t("help", l) for l in LANG])
async def help_menu(msg: types.Message):
    lang = await get_lang(msg.from_user.id)
    await msg.answer(t("help_text", lang), reply_markup=main_menu(lang))

# ---------- /wallet Command ----------
@dp.message_handler(commands=['wallet'])
async def wallet_cmd(msg: types.Message):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang, wallet FROM users WHERE user_id=$1", msg.from_user.id)
        lang = u["lang"] if u else "en"
    if u and u["wallet"]:
        await msg.answer(f"🔗 {t('your_wallet', lang)}: <code>{u['wallet']}</code>", parse_mode="HTML")
    else:
        await msg.answer(t("no_wallet", lang) + "\\n" + t("add_wallet_hint", lang))
'''

# מכניסים אחרי process_wallet (או לפני main)
insert_after = code.find('async def process_wallet(msg: types.Message, state: FSMContext):')
if insert_after != -1:
    # נמצא סוף הפונקציה
    end_of_func = code.find('\n# ========== /share ==========', insert_after)
    if end_of_func == -1:
        end_of_func = code.find('async def main():', insert_after)
    code = code[:end_of_func] + new_handlers + '\n' + code[end_of_func:]

# 5. הגנת FSM: במידה והטקסט הוא תווית תפריט – צא מה-FSM
# נוסיף בדיקה בתחילת כל handler של FSM.
for state_func in ['async def process_name', 'async def process_prof', 'async def process_wallet']:
    # מוצאים את השורה "async def process_..."
    start = code.find(state_func)
    if start == -1: continue
    # מוצאים את תחילת גוף הפונקציה (אחרי השורה של def)
    body_start = code.find('\n', start) + 1
    indent = '    '  # הנחה שהזחה של 4 רווחים
    # נוסיף קוד בדיקה
    protection_code = f'''    # FSM protection: cancel if menu label pressed
    data = await state.get_data()
    lang = data.get("lang", "en")
    if msg.text in MENU_LABELS:
        await state.finish()
        await msg.answer(t("cancelled_due_to_menu", lang), reply_markup=main_menu(lang))
        return
'''
    code = code[:body_start] + protection_code + code[body_start:]

# 6. תיקון קובץ lang.json – תרגומים אמיתיים (אם ריק)
try:
    with open('lang.json', 'r', encoding='utf-8') as f:
        lang_data = json.load(f)
except:
    lang_data = {}

# מוודא שיש מפתחות בסיסיים
required_keys = {
    "welcome": {"en": "Welcome!", "he": "ברוך הבא!"},
    "choose_lang": {"en": "Choose language:", "he": "בחר שפה:"},
    "help_text": {"en": "I am NIFTI, your digital business card.", "he": "אני NIFTI, כרטיס הביקור הדיגיטלי שלך."},
    "create_card": {"en": "Create Free Card", "he": "צור כרטיס חינם"},
    "my_card": {"en": "My Card", "he": "הכרטיס שלי"},
    "premium": {"en": "Premium Products", "he": "מוצרי פרימיום"},
    "earnings": {"en": "My Earnings", "he": "הרווחים שלי"},
    "leaderboard": {"en": "Leaderboard", "he": "לוח מובילים"},
    "settings_menu": {"en": "Settings", "he": "הגדרות"},
    "help": {"en": "Help", "he": "עזרה"},
    "card_name": {"en": "What name?", "he": "מה השם?"},
    "card_prof": {"en": "Profession?", "he": "מקצוע?"},
    "card_wallet": {"en": "TON wallet address", "he": "כתובת ארנק TON"},
    "card_done": {"en": "Card created!", "he": "הכרטיס נוצר!"},
    "no_card": {"en": "No card yet.", "he": "אין כרטיס עדיין."},
    "cancel_msg": {"en": "Cancelled.", "he": "בוטל."},
    "cancelled_due_to_menu": {"en": "Cancelled, returning to menu.", "he": "בוטל, חוזר לתפריט."},
    "premium_info": {"en": "Premium features coming soon.", "he": "תכונות פרימיום בקרוב."},
    "your_wallet": {"en": "Your wallet", "he": "הארנק שלך"},
    "no_wallet": {"en": "No wallet connected.", "he": "אין ארנק מחובר."},
    "add_wallet_hint": {"en": "Use /settings to add one.", "he": "השתמש ב-/settings כדי להוסיף."},
    "invalid_wallet": {"en": "Invalid TON address.", "he": "כתובת TON לא תקינה."},
    "wallet_updated": {"en": "Wallet updated!", "he": "הארנק עודכן!"},
    "name_updated": {"en": "Name updated.", "he": "השם עודכן."},
    "prof_updated": {"en": "Profession updated.", "he": "המקצוע עודכן."},
    "setprice_prompt": {"en": "Your current price: {price} TON", "he": "המחיר הנוכחי: {price} TON"},
    "setprice_done": {"en": "Price set to {price} TON.", "he": "המחיר נקבע ל-{price} TON."},
    "market": {"en": "Market:\\n{sellers}", "he": "שוק:\\n{sellers}"},
    "market_empty": {"en": "No cards for sale yet.", "he": "אין כרטיסים למכירה עדיין."},
}

for key, translations in required_keys.items():
    if key not in lang_data:
        lang_data[key] = translations
    else:
        for lang_code in translations:
            if lang_code not in lang_data[key]:
                lang_data[key][lang_code] = translations[lang_code]

with open('lang.json', 'w', encoding='utf-8') as f:
    json.dump(lang_data, f, ensure_ascii=False, indent=2)

print("✅ lang.json updated")

# --- write back bot.py ---
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ bot.py fully upgraded!")