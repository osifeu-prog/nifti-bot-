import time
import telebot
from config import BOT_TOKEN
from app.core.logging.logger import log
from app.services.user_service import UserService

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    UserService.create_user(user_id, username)

    user = UserService.get_user(user_id)

    bot.send_message(
        message.chat.id,
        f"""?? NIFTI STABLE ENGINE

User: {username}
ID: {user_id}

Balance: {user["balance"] if user else 0}

Status: STABLE SAAS ACTIVE"""
    )

def run_bot():
    log("BOT START STABLE LAYER")

    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            log(f"BOT ERROR: {e}", "ERROR")
            time.sleep(3)

