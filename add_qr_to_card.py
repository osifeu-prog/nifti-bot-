with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

qr_html = '''
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=ton://transfer/{TON_WALLET}?amount={amount_nano}&text=NIFTI_PAY:{user_id}" alt="QR Code" style="margin-top:15px;border-radius:10px;">
'''

# Insert after the Pay button
old_btn = '''<button class="btn" onclick="window.open('https://app.tonkeeper.com/transfer/{TON_WALLET}?amount={amount_nano}&text=NIFTI_PAY:{user_id}', '_blank')">?? Pay with TON</button>'''
new_btn = old_btn + qr_html

if qr_html not in content:
    content = content.replace(old_btn, new_btn)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('QR added to card page.')
else:
    print('Already present.')
