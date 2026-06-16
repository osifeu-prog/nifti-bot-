def register(bot):

    @bot.message_handler(commands=["status"])
    def status(message):
        bot.send_message(message.chat.id, "? V15 SYSTEM ONLINE")

