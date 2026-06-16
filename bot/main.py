import telebot
from config import BOT_TOKEN
from core.engine import engine

bot = telebot.TeleBot(BOT_TOKEN)

def add_user(user_id, username):
    engine.execute("""
        INSERT INTO users (id, username)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (user_id, username))


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    add_user(user_id, username)

    bot.send_message(
        message.chat.id,
        f"""?? NIFTI V6 ARCH

User: {username}
ID: {user_id}

Status: ACTIVE"""
    )


@bot.message_handler(commands=["status"])
def status(message):
    bot.send_message(message.chat.id, "?? NIFTI V6 ONLINE")


def run_bot():
    print("[BOT] RUNNING V6")
    bot.infinity_polling(skip_pending=True)

