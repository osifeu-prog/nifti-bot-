import telebot
import requests
from config import BOT_TOKEN
from core.config.lang import t

API = "http://127.0.0.1:8000"
bot = telebot.TeleBot(BOT_TOKEN)

def get_lang(user):
    return "en"  # TODO: later DB

@bot.message_handler(commands=["start"])
def start(m):
    lang = get_lang(m.from_user.id)

    try:
        r = requests.get(f"{API}/ledger/{m.from_user.id}").json()
        balance = r.get("balance", 0)

        text = f"""
{t(lang,'welcome')}

Balance: {balance}
"""
        bot.send_message(m.chat.id, text)

    except:
        bot.send_message(m.chat.id, t(lang,"system_not_ready"))

def run():
    print("[BOT] STARTED")
    bot.infinity_polling()

