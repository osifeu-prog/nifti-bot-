from app.services.users import UserService

def register(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"

        UserService.create_user(user_id, username)

        bot.send_message(
            message.chat.id,
            f"""?? NIFTI V15 SAAS ENGINE

User: {username}
ID: {user_id}

Status: LIVE PRODUCTION READY"""
        )

