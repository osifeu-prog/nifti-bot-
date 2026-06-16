import asyncio, os
from flask import Flask, render_template, request, redirect, flash, url_for
import nifti_core as core
from aiogram import Bot

app = Flask(__name__)
app.secret_key = os.urandom(24)

ADMIN_ID = int(os.getenv('ADMIN_USER_ID', '224223270'))

async def get_users():
    await core.create_pool()
    async with core.pool.acquire() as conn:
        rows = await conn.fetch('SELECT user_id, card_name, card_prof, wallet, balance FROM users ORDER BY user_id')
        return [dict(r) for r in rows]

async def get_payments():
    await core.create_pool()
    async with core.pool.acquire() as conn:
        rows = await conn.fetch('SELECT * FROM payments ORDER BY id DESC LIMIT 20')
        return [dict(r) for r in rows]

async def send_broadcast(text):
    token = os.getenv('BOT_TOKEN')
    bot = Bot(token=token)
    await core.create_pool()
    async with core.pool.acquire() as conn:
        users = await conn.fetch('SELECT user_id FROM users')
    sent, failed = 0, 0
    for u in users:
        try:
            await bot.send_message(u['user_id'], text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await bot.close()
    return sent, failed

@app.route('/')\n@app.route('/admin')
def index():
    users = asyncio.run(get_users())
    payments = asyncio.run(get_payments())
    return render_template('admin.html', users=users, payments=payments)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    message = request.form.get('message', '').strip()
    if not message:
        flash('Message cannot be empty.')
        return redirect(url_for('index'))
    sent, failed = asyncio.run(send_broadcast(message))
    flash(f'Broadcast sent: {sent} delivered, {failed} failed.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)

