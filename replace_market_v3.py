# replace_market_v3.py
lines = open(r"D:\NIFTI\server.py", "r", encoding="utf-8").readlines()

# Find start and end of market_cmd function
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
    exit()

new_func_lines = [
    "async def market_cmd(msg: types.Message):\n",
    "    from services.marketplace import list_products\n",
    "    try:\n",
    "        products = await list_products()\n",
    "    except Exception as e:\n",
    '        await msg.answer(f"Error loading products: {e}")\n',
    "        return\n",
    "    if not products:\n",
    '        await msg.answer("No products available.")\n',
    "        return\n",
    "    for p in products[:10]:\n",
    '        text = f"**{p[\'name\']}**\n{p[\'description\']}\nPrice: {p[\'price\']} TON"\n',
    "        kb = types.InlineKeyboardMarkup().add(\n",
    '            types.InlineKeyboardButton("Buy", callback_data=f"buy_{p[\'id\']}")\n',
    "        )\n",
    '        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)\n',
    "\n",
]

new_lines = lines[:start] + new_func_lines + lines[end:]
with open(r"D:\NIFTI\server.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("market_cmd replaced successfully")
