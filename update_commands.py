import asyncio, aiohttp, os

BOT_TOKEN = os.getenv("BOT_TOKEN", "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def set_commands():
    commands = [
        {"command": "start", "description": "Main menu"},
        {"command": "my_card", "description": "View your card"},
        {"command": "edit_card", "description": "Edit your card"},
        {"command": "set_photo", "description": "Upload photo"},
        {"command": "market", "description": "Buy cards"},
        {"command": "earnings", "description": "Balance"},
        {"command": "leaderboard", "description": "Top users"},
        {"command": "referrals", "description": "Your refs"},
        {"command": "invite", "description": "Get QR link"},
        {"command": "set_price", "description": "Set price"},
        {"command": "spin", "description": "Slot machine"},
        {"command": "status", "description": "Stats"},
        # SIF commands
        {"command": "sif", "description": "Your SIF balance"},
        {"command": "buy_sif", "description": "Buy SIF with TON"},
        {"command": "sell_sif", "description": "Sell SIF for TON"},
        {"command": "set_sif_rate", "description": "(Admin) Set SIF rate"},
    ]
    url = f"{API}/setMyCommands"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"commands": commands}) as resp:
            print(await resp.json())

asyncio.run(set_commands())
