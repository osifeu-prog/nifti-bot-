with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the broken QR endpoint if it exists
import re
content = re.sub(r'@app\.get\("/api/qr/\{user_id\}"\).*?(?=\n# |\nfrom |\napp\.mount|\n@app\.|\nif __name__|\Z)', '', content, flags=re.DOTALL)

# Now inject the correct QR endpoint just before if __name__ == '__main__'
correct_qr = '''
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

main_pos = content.find("if __name__ == '__main__':")
if main_pos != -1:
    content = content[:main_pos] + correct_qr + '\n\n' + content[main_pos:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Broken QR endpoint replaced with correct version.')
