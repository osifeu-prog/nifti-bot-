import asyncio, os, logging, aiohttp
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="NIFTI Bot")

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def send_telegram_message(chat_id: int, text: str, reply_markup=None):
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN not set!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

# ==================== MINI APP ====================
app.mount("/app/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/app")
@app.get("/app/{full_path:path}")
async def serve_mini_app(request: Request):
    user_id = request.query_params.get("user_id")
    logging.info(f"MINI-APP ACCESS - user_id: {user_id}")
    try:
        html = open("frontend/dist/index.html", encoding="utf-8").read()
        import time
        ts = int(time.time())
        html = html.replace('.js"', f'.js?v={ts}"')
        html = html.replace('.css"', f'.css?v={ts}"')
        if user_id:
            injection = f'<script>window.NIFTI_USER_ID = "{user_id}"; console.log("✅ Injected ID: {user_id}");</script>'
            html = html.replace("<script", injection + "<script", 1)
        return HTMLResponse(html, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    except Exception as e:
        logging.error(f"Frontend error: {e}")
        return HTMLResponse("<h1>Frontend Error</h1>", 404)

# ==================== API ====================
@app.get("/api/card/{user_id}")
async def api_card_json(user_id: int):
    return {"card_name": f"User {user_id}", "card_prof": "NIFTI Member", "wallet": "Not linked"}

@app.get("/api/qr/{user_id}")
async def api_qr_json(user_id: int):
    return {"qr_url": "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=ton://transfer/test", "amount_ton": 1.0}

# ==================== WEBHOOK ====================
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        
        logging.info(f"Received from {chat_id}: {text}")

        if text == "/start":
            keyboard = {
                "inline_keyboard": [[
                    {"text": "🃏 Open My NIFTI Card", "web_app": {"url": "https://bot-production-c2a5.up.railway.app/app?user_id=" + str(chat_id)}}
                ]]
            }
            await send_telegram_message(
                chat_id, 
                "✅ <b>Welcome to NIFTI!</b>\n\nPress the button below to open your card:",
                keyboard
            )
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok", "message": "NIFTI Bot is running"}

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8000))
    logging.info(f"🚀 Starting on port {port}")
    uvicorn.run(app, host='0.0.0.0', port=port)
