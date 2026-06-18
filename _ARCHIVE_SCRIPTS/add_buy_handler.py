# add_buy_handler.py
server_path = r"D:\NIFTI\server.py"

with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

# Handler code to insert before "if __name__"
handler_code = """

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_buy(call: types.CallbackQuery):
    from services.marketplace import buy_product
    product_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    result = await buy_product(user_id, product_id)
    if result['ok']:
        await call.message.answer(
            f"✅ Purchased {result['product']} for {result['price']} TON (fee: {result['fee']} TON)"
        )
    else:
        await call.message.answer(f"❌ {result['error']}")
"""

# Insert right before "if __name__ == '__main__':"
insert_pos = content.rfind("if __name__ == '__main__':")
if insert_pos == -1:
    insert_pos = len(content)
content = content[:insert_pos] + handler_code + "\n" + content[insert_pos:]

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)

print("buy handler added")
