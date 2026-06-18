import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

qr_endpoint = r'''
@app.get("/api/qr/{user_id}")
async def get_payment_qr(user_id: int):
    async with core.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT wallet, price FROM users WHERE user_id = \", user_id)
    if not row:
        return {"error": "User not found"}
    wallet = row['wallet'] or TON_WALLET
    amount_nano = int(float(row['price'] or 1) * 1e9)
    memo = f"NIFTI_PAY:{user_id}"
    ton_link = f"ton://transfer/{wallet}?amount={amount_nano}&text={memo}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={ton_link}"
    return {"qr_url": qr_url, "ton_link": ton_link, "amount_ton": row['price'], "wallet": wallet}
'''

# Insert after the /api/card endpoint
if '/api/qr/' not in content:
    content = content.replace(
        'return {"card_name": row["card_name"], "card_prof": row["card_prof"], "wallet": row["wallet"]}',
        'return {"card_name": row["card_name"], "card_prof": row["card_prof"], "wallet": row["wallet"]}' + qr_endpoint
    )
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('QR endpoint injected.')
else:
    print('QR endpoint already exists.')
