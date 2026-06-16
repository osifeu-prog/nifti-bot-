import re
import json

# --- read bot.py ---
with open('bot.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. ×•×•×“× ×©×”-regex ×‘-is_valid_ton × ×§×™
code = code.replace(r'^[UE]Q[A-Za-z0-9_-]{46}\$', r'^[UE]Q[A-Za-z0-9_-]{46}$')

# 2. ×”×•×¡×¤×ª ×¤×•× ×§×¦×™×™×ª get_lang (×× ×œ× ×§×™×™×ž×ª)
if 'async def get_lang' not in code:
    get_lang_func = '''
async def get_lang(user_id):
    async with pool.acquire() as conn:
        u = await conn.fetchrow("SELECT lang FROM users WHERE user_id=$1", user_id)
        return u["lang"] if u else "en"
'''
    # ×ž×›× ×™×¡×™× ××—×¨×™ ×”×¤×•× ×§×¦×™×” my_card_cmd (××• ×œ×¤× ×™ main)
    insert_point = code.find('async def main():')
    if insert_point == -1:
        insert_point = code.find('if __name__')
    code = code[:insert_point] + get_lang_func + '\n' + code[insert_point:]

# 3. ×¨×©×™×ž×ª ×›×œ ×ª×•×•×™×•×ª ×”×ª×¤×¨×™×˜ (×œ×¡×™× ×•×Ÿ FSM)
menu_keys = ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"]
menu_labels_code = '''
# Auto-generated menu labels
MENU_LABELS = set()
for lang in LANG:
    for key in ["create_card","my_card","premium","earnings","leaderboard","settings_menu","help"]:
        MENU_LABELS.add(LANG[lang].get(key, ""))
'''
# ×ž×›× ×™×¡×™× ××—×¨×™ load_lang
if 'MENU_LABELS' not in code:
    code = code.replace('def load_lang():', 'def load_lang():\n    global MENU_LABELS\n    ' + menu_keys.__str__() + '  # placeholder\n')  # not needed, simpler: just insert the block after load_lang
    # Insert after load_lang function
    load_lang_end = code.find('async def create_pool():')
    if load_lang_end == -1:
        load_lang_end = code.find('# ==========')
    code = code[:load_lang_end] + menu_labels_code + '\n' + code[load_lang_end:]

# 4. ×”×•×¡×¤×ª handlers ×œ×›×¤×ª×•×¨×™ ×”×ª×¤×¨×™×˜
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
        await msg.answer(f"ðŸ”— {t('your_wallet', lang)}: <code>{u['wallet']}</code>", parse_mode="HTML")
    else:
        await msg.answer(t("no_wallet", lang) + "\\n" + t("add_wallet_hint", lang))
'''

# ×ž×›× ×™×¡×™× ××—×¨×™ process_wallet (××• ×œ×¤× ×™ main)
insert_after = code.find('async def process_wallet(msg: types.Message, state: FSMContext):')
if insert_after != -1:
    # × ×ž×¦× ×¡×•×£ ×”×¤×•× ×§×¦×™×”
    end_of_func = code.find('\n# ========== /share ==========', insert_after)
    if end_of_func == -1:
        end_of_func = code.find('async def main():', insert_after)
    code = code[:end_of_func] + new_handlers + '\n' + code[end_of_func:]

# 5. ×”×’× ×ª FSM: ×‘×ž×™×“×” ×•×”×˜×§×¡×˜ ×”×•× ×ª×•×•×™×ª ×ª×¤×¨×™×˜ â€“ ×¦× ×ž×”-FSM
# × ×•×¡×™×£ ×‘×“×™×§×” ×‘×ª×—×™×œ×ª ×›×œ handler ×©×œ FSM.
for state_func in ['async def process_name', 'async def process_prof', 'async def process_wallet']:
    # ×ž×•×¦××™× ××ª ×”×©×•×¨×” "async def process_..."
    start = code.find(state_func)
    if start == -1: continue
    # ×ž×•×¦××™× ××ª ×ª×—×™×œ×ª ×’×•×£ ×”×¤×•× ×§×¦×™×” (××—×¨×™ ×”×©×•×¨×” ×©×œ def)
    body_start = code.find('\n', start) + 1
    indent = '    '  # ×”× ×—×” ×©×”×–×—×” ×©×œ 4 ×¨×•×•×—×™×
    # × ×•×¡×™×£ ×§×•×“ ×‘×“×™×§×”
    protection_code = f'''    # FSM protection: cancel if menu label pressed
    data = await state.get_data()
    lang = data.get("lang", "en")
    if msg.text in MENU_LABELS:
        await state.finish()
        await msg.answer(t("cancelled_due_to_menu", lang), reply_markup=main_menu(lang))
        return
'''
    code = code[:body_start] + protection_code + code[body_start:]

# 6. ×ª×™×§×•×Ÿ ×§×•×‘×¥ lang.json â€“ ×ª×¨×’×•×ž×™× ××ž×™×ª×™×™× (×× ×¨×™×§)
try:
    with open('lang.json', 'r', encoding='utf-8') as f:
        lang_data = json.load(f)
except:
    lang_data = {}

# ×ž×•×•×“× ×©×™×© ×ž×¤×ª×—×•×ª ×‘×¡×™×¡×™×™×
required_keys = {
    "welcome": {"en": "Welcome!", "he": "×‘×¨×•×š ×”×‘×!"},
    "choose_lang": {"en": "Choose language:", "he": "×‘×—×¨ ×©×¤×”:"},
    "help_text": {"en": "I am NIFTI, your digital business card.", "he": "×× ×™ NIFTI, ×›×¨×˜×™×¡ ×”×‘×™×§×•×¨ ×”×“×™×’×™×˜×œ×™ ×©×œ×š."},
    "create_card": {"en": "Create Free Card", "he": "×¦×•×¨ ×›×¨×˜×™×¡ ×—×™× ×"},
    "my_card": {"en": "My Card", "he": "×”×›×¨×˜×™×¡ ×©×œ×™"},
    "premium": {"en": "Premium Products", "he": "×ž×•×¦×¨×™ ×¤×¨×™×ž×™×•×"},
    "earnings": {"en": "My Earnings", "he": "×”×¨×•×•×—×™× ×©×œ×™"},
    "leaderboard": {"en": "Leaderboard", "he": "×œ×•×— ×ž×•×‘×™×œ×™×"},
    "settings_menu": {"en": "Settings", "he": "×”×’×“×¨×•×ª"},
    "help": {"en": "Help", "he": "×¢×–×¨×”"},
    "card_name": {"en": "What name?", "he": "×ž×” ×”×©×?"},
    "card_prof": {"en": "Profession?", "he": "×ž×§×¦×•×¢?"},
    "card_wallet": {"en": "TON wallet address", "he": "×›×ª×•×‘×ª ××¨× ×§ TON"},
    "card_done": {"en": "Card created!", "he": "×”×›×¨×˜×™×¡ × ×•×¦×¨!"},
    "no_card": {"en": "No card yet.", "he": "××™×Ÿ ×›×¨×˜×™×¡ ×¢×“×™×™×Ÿ."},
    "cancel_msg": {"en": "Cancelled.", "he": "×‘×•×˜×œ."},
    "cancelled_due_to_menu": {"en": "Cancelled, returning to menu.", "he": "×‘×•×˜×œ, ×—×•×–×¨ ×œ×ª×¤×¨×™×˜."},
    "premium_info": {"en": "Premium features coming soon.", "he": "×ª×›×•× ×•×ª ×¤×¨×™×ž×™×•× ×‘×§×¨×•×‘."},
    "your_wallet": {"en": "Your wallet", "he": "×”××¨× ×§ ×©×œ×š"},
    "no_wallet": {"en": "No wallet connected.", "he": "××™×Ÿ ××¨× ×§ ×ž×—×•×‘×¨."},
    "add_wallet_hint": {"en": "Use /settings to add one.", "he": "×”×©×ª×ž×© ×‘-/settings ×›×“×™ ×œ×”×•×¡×™×£."},
    "invalid_wallet": {"en": "Invalid TON address.", "he": "×›×ª×•×‘×ª TON ×œ× ×ª×§×™× ×”."},
    "wallet_updated": {"en": "Wallet updated!", "he": "×”××¨× ×§ ×¢×•×“×›×Ÿ!"},
    "name_updated": {"en": "Name updated.", "he": "×”×©× ×¢×•×“×›×Ÿ."},
    "prof_updated": {"en": "Profession updated.", "he": "×”×ž×§×¦×•×¢ ×¢×•×“×›×Ÿ."},
    "setprice_prompt": {"en": "Your current price: {price} TON", "he": "×”×ž×—×™×¨ ×”× ×•×›×—×™: {price} TON"},
    "setprice_done": {"en": "Price set to {price} TON.", "he": "×”×ž×—×™×¨ × ×§×‘×¢ ×œ-{price} TON."},
    "market": {"en": "Market:\\n{sellers}", "he": "×©×•×§:\\n{sellers}"},
    "market_empty": {"en": "No cards for sale yet.", "he": "××™×Ÿ ×›×¨×˜×™×¡×™× ×œ×ž×›×™×¨×” ×¢×“×™×™×Ÿ."},
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

print("âœ… lang.json updated")

# --- write back bot.py ---
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("âœ… bot.py fully upgraded!")

