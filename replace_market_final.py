# replace_market_final.py
import os, sys

server_path = r"D:\NIFTI\server.py"

with open(server_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start = None
end = None
for i, line in enumerate(lines):
    if line.strip().startswith("async def market_cmd(msg: types.Message):"):
        start = i
    if start is not None and line.strip().startswith("# ----------"):
        end = i
        break

if start is None or end is None:
    print("Could not locate market_cmd function boundaries")
    sys.exit(1)

new_func = """async def market_cmd(msg: types.Message):
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
        text = f"**{p['name']}**\\n{p['description']}\\nPrice: {p['price']} TON"
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Buy", callback_data=f"buy_{p['id']}")
        )
        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)
"""

new_lines = [line + "\n" for line in new_func.splitlines()]
new_lines.append("\n")  # blank line after function

result = lines[:start] + new_lines + lines[end:]
with open(server_path, "w", encoding="utf-8") as f:
    f.writelines(result)

print("market_cmd replaced successfully")
