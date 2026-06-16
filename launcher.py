import os, subprocess, threading, time, sys, re, logging, asyncio
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NIFTI")

# BOT_TOKEN loaded from .env
os.environ.setdefault("ADMIN_USER_ID", "224223270")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")

# --------------- Start Cloudflare Tunnel ---------------
def start_tunnel():
    logger.info("??  Starting Cloudflare Tunnel...")
    proc = subprocess.Popen(
        [r".\cloudflared.exe", "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        logger.debug(line.strip())
        m = re.search(r'https://[^ ]+\.trycloudflare\.com', line)
        if m:
            url = m.group(0)
            logger.info(f"Tunnel URL: {url}")
            os.environ["TUNNEL_URL"] = url
            # Update Telegram menu button
            import requests
            payload = {
                "chat_menu_button": {
                    "type": "web_app",
                    "text": "??? ?? NIFTI",
                    "web_app": {"url": url}
                }
            }
            requests.post(
                f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/setChatMenuButton",
                json=payload
            )
            return url
    logger.error("Tunnel process ended without URL")
    return None

# --------------- Start TON Scanner ---------------
def start_scanner():
    logger.info("?? Starting TON Scanner...")
    import ton_scanner
    asyncio.run(ton_scanner.main())

# --------------- Start API on port 8001 ---------------
def start_api():
    logger.info("?? Starting API server on port 8001...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info")

# --------------- Start Bot (webhook) ---------------
def start_bot():
    logger.info("?? Starting Bot (webhook mode)...")
    import bot
    from aiogram.utils.executor import start_webhook
    start_webhook(
        dispatcher=bot.dp,
        webhook_path="/webhook",
        on_startup=bot.on_startup,
        on_shutdown=bot.on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=8000,
    )

if __name__ == "__main__":
    # 1. Start tunnel and wait for URL
    tunnel_url = start_tunnel()
    if not tunnel_url:
        logger.error("Cannot continue without tunnel URL")
        sys.exit(1)

    # 2. Start scanner in a daemon thread
    scanner_thread = threading.Thread(target=start_scanner, daemon=True)
    scanner_thread.start()

    # 3. Start API in a daemon thread
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # 4. Start Bot (main thread  blocks until Ctrl+C)
    start_bot()
