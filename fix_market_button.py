import re

with open(r"D:\NIFTI\server.py", "r", encoding="utf-8") as f:
    content = f.read()

# החלף את הפונקציה market_cmd
old = r'async def market_cmd\(msg: types\.Message\):.*?(?=\n# ----------)'
new = '''async def market_cmd(msg: types.Message):
    from services.marketplace import list_products
    try:
        products = await list_products()
    except Exception as e:
        await msg.answer(f"Error loading products: {e}")
        return
    if not products:
        await msg.answer("No products available.")
        return
    for p in products[:10]:
        text = f'**{p["name"]}**\n{p["description"]}\nPrice: {p["price"]} TON'
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Buy", callback_data=f"buy_{p[\"id\"]}")
        )
        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)
'''

content = re.sub(old, new, content, flags=re.DOTALL)

with open(r"D:\NIFTI\server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("market_cmd fixed  now includes Buy button")
