lines = open(r"D:\NIFTI\server.py", "r", encoding="utf-8").readlines()

start = None
end = None
for i, line in enumerate(lines):
    if line.strip().startswith("async def market_cmd(msg: types.Message):"):
        start = i
    if start is not None and i > start and line.strip() == "" and lines[i-1].strip() != "":
        end = i
        break

if start is None or end is None:
    print("Could not find market_cmd function")
    exit()

new_func = [
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
    '        text = f"**{p[\'name\']}**\\\\n{p[\'description\']}\\\\nPrice: {p[\'price\']} TON"\n',
    "        kb = types.InlineKeyboardMarkup().add(\n",
    '            types.InlineKeyboardButton("Buy", callback_data=f"buy_{p[\'id\']}")\n',
    "        )\n",
    '        await msg.answer(text, parse_mode="Markdown", reply_markup=kb)\n',
    "\n",
]

new_lines = lines[:start] + new_func + lines[end+1:]
with open(r"D:\NIFTI\server.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("market_cmd replaced successfully")
