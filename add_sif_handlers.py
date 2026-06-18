# add_sif_handlers.py
server_path = r"D:\NIFTI\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

sif_handlers = """

# ---------- SIF Token Handlers ----------
from services.sif_token import get_sif_balance, buy_sif, sell_sif, transfer_sif, set_sif_rate, get_sif_rate

@dp.message_handler(commands=['sif'])
async def sif_status(msg: types.Message):
    user_id = msg.from_user.id
    bal = await get_sif_balance(user_id)
    rate = await get_sif_rate()
    await msg.answer(f"💎 SIF Balance: {bal} SIF\nRate: 1 TON = {rate} SIF")

@dp.message_handler(commands=['buy_sif'])
async def cmd_buy_sif(msg: types.Message):
    try:
        _, amount_str = msg.text.split()
        ton_amount = float(amount_str)
        result = await buy_sif(msg.from_user.id, ton_amount)
        if result['ok']:
            await msg.answer(f"✅ Bought {result['sif_received']} SIF for {result['ton_spent']} TON (rate: {result['rate']})")
        else:
            await msg.answer(f"❌ {result['error']}")
    except:
        await msg.answer("Usage: /buy_sif <ton_amount>")

@dp.message_handler(commands=['sell_sif'])
async def cmd_sell_sif(msg: types.Message):
    try:
        _, amount_str = msg.text.split()
        sif_amount = float(amount_str)
        result = await sell_sif(msg.from_user.id, sif_amount)
        if result['ok']:
            await msg.answer(f"✅ Sold {result['sif_sold']} SIF for {result['ton_received']} TON")
        else:
            await msg.answer(f"❌ {result['error']}")
    except:
        await msg.answer("Usage: /sell_sif <sif_amount>")

@dp.message_handler(commands=['set_sif_rate'])
async def cmd_set_sif_rate(msg: types.Message):
    from core.pool import acquire
    async with core.pool.acquire() as conn:
        role = await conn.fetchval('SELECT role FROM users WHERE user_id = $1', msg.from_user.id)
    if role != 'admin':
        await msg.answer("Admin only.")
        return
    try:
        _, rate_str = msg.text.split()
        new_rate = float(rate_str)
        await set_sif_rate(new_rate)
        await msg.answer(f"✅ SIF rate set to: 1 TON = {new_rate} SIF")
    except:
        await msg.answer("Usage: /set_sif_rate <rate>")
"""

# Insert before if __name__
pos = content.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = len(content)
content = content[:pos] + sif_handlers + "\n" + content[pos:]

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)
print("SIF handlers added")
