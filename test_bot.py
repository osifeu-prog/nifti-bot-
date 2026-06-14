import asyncio, json, os, asyncpg, unittest
from unittest.mock import patch
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat
import importlib.util

spec = importlib.util.spec_from_file_location("bot", "bot.py")
bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot_module)

bot = Bot(token="123456:ABC-DEF1234gh", parse_mode="HTML")
Bot.set_current(bot)
Dispatcher.set_current(bot_module.dp)
BASE_USER_ID = 224223270

class TestNiftiBot(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dp = bot_module.dp
        self.dp.bot = bot
        self.dp.storage = MemoryStorage()
        Dispatcher.set_current(self.dp)
        self.sent_messages = []
        patcher = patch('aiogram.Bot.send_message', new=self.mock_send_message)
        patcher.start()
        self.addCleanup(patcher.stop)
        bot_module.pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
        bot_module.load_lang()
        bot_module.ADMIN_ID = BASE_USER_ID

    async def mock_send_message(self, chat_id, text, **kwargs):
        msg = Message(); msg.text = text; msg.chat = Chat(id=chat_id, type='private'); msg.from_user = User(id=999, is_bot=True, first_name="Bot")
        self.sent_messages.append(msg); return msg

    async def send_cmd(self, cmd, user_id):
        self.sent_messages.clear()
        msg = Message(
            text=cmd,
            chat=Chat(id=user_id, type='private'),
            from_user=User(id=user_id, is_bot=False, first_name="Test", last_name=None, username=None, language_code="en")
        )
        update = types.Update(update_id=1, message=msg)
        await self.dp.process_update(update)
        return self.sent_messages[-1].text if self.sent_messages else ""

    async def test_guide_translation(self):
        uid = BASE_USER_ID
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        resp = await self.send_cmd("/guide", uid)
        self.assertIn("Why NIFTI", resp)

    async def asyncTearDown(self):
        await bot_module.pool.close()

if __name__ == "__main__":
    unittest.main()
