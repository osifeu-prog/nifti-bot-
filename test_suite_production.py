import asyncio, json, os, asyncpg, unittest, re, time
from unittest.mock import Mock, patch
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat, Update
import importlib.util

spec = importlib.util.spec_from_file_location("bot", "bot.py")
bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot_module)

bot = Bot(token="123456:ABC-DEF1234gh", parse_mode="HTML")
BASE_USER_ID = 224223270
ADMIN_ID = BASE_USER_ID

class TestNiftiProduction(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dp = bot_module.dp
        self.dp.bot = bot
        self.dp.storage = MemoryStorage()
        Dispatcher.set_current(self.dp)

        self.sent_messages = []
        patcher = patch('aiogram.Bot.send_message', new=self.mock_send_message)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.edit_patcher = patch('aiogram.Bot.edit_message_text', return_value=None)
        self.edit_patcher.start()
        self.addCleanup(self.edit_patcher.stop)
        self.callback_patcher = patch('aiogram.Bot.answer_callback_query', return_value=None)
        self.callback_patcher.start()
        self.addCleanup(self.callback_patcher.stop)

        bot_module.pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
        bot_module.LANG = {}
        bot_module.load_lang()
        bot_module.ADMIN_ID = ADMIN_ID

    async def mock_send_message(self, chat_id, text, **kwargs):
        msg = Mock()
        msg.text = text
        msg.chat = Mock(id=chat_id, type='private')
        msg.from_user = Mock(id=999, is_bot=True, first_name="Bot")
        self.sent_messages.append(msg)
        return msg

    async def send_cmd(self, cmd, user_id):
        self.sent_messages.clear()
        # Build mock message
        mock_msg = Mock()
        mock_msg.text = cmd
        mock_msg.chat = Mock(id=user_id, type='private')
        mock_msg.from_user = Mock(id=user_id, is_bot=False, first_name="Test")
        mock_msg.message_id = 1
        mock_msg.date = int(time.time())
        mock_msg.bot = bot
        mock_msg.answer = lambda *a, **kw: bot.send_message(*a, **kw)  # fallback if needed

        update = Update(update_id=1, message=mock_msg)
        await self.dp.process_update(update)
        return self.sent_messages[-1].text if self.sent_messages else ""

    def t(self, key, lang="en"):
        return bot_module.t(key, lang)

    # ================== TESTS ==================

    def test_ton_address_validation(self):
        valid = "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
        self.assertTrue(bot_module.is_valid_ton(valid))
        self.assertFalse(bot_module.is_valid_ton("UQCr743g"))
        self.assertFalse(bot_module.is_valid_ton(""))

    def test_financial_math(self):
        self.assertEqual(bot_module.platform_fee(10.0), 2.0)
        self.assertEqual(bot_module.seller_amount(10.0), 8.0)

    def test_translation_fallback(self):
        self.assertEqual(self.t("non_existent_key_test", "he"), "non_existent_key_test")

    def test_all_languages_loaded(self):
        self.assertIn("en", bot_module.LANG)
        self.assertEqual(len(bot_module.LANG), 8)

    async def test_guide_en(self):
        uid = BASE_USER_ID
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        resp = await self.send_cmd("/guide", uid)
        self.assertIn("Why NIFTI", resp)

    async def test_card_creation_fsm(self):
        uid = BASE_USER_ID + 1
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        resp = await self.send_cmd(self.t("create_card","en"), uid)
        self.assertIn("What name?", resp)
        self.assertIn("CardForm:waiting_name", str(await state.get_state()))
        resp = await self.send_cmd("Osif Test", uid)
        self.assertIn("Profession?", resp)
        self.assertIn("CardForm:waiting_prof", str(await state.get_state()))
        resp = await self.send_cmd("Artist", uid)
        self.assertIn("TON wallet address", resp)
        self.assertIn("CardForm:waiting_wallet", str(await state.get_state()))
        resp = await self.send_cmd("UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp", uid)
        self.assertIn("Card created!", resp)
        self.assertIsNone(await state.get_state())

    async def test_cancel_fsm(self):
        uid = BASE_USER_ID + 2
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        await self.send_cmd(self.t("create_card","en"), uid)
        await self.send_cmd("Test Name", uid)
        self.assertIn("waiting_prof", str(await state.get_state()))
        resp = await self.send_cmd("/cancel", uid)
        self.assertIn("Cancelled", resp)
        self.assertIsNone(await state.get_state())

    async def test_admin_protection(self):
        uid = BASE_USER_ID + 99
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        resp = await self.send_cmd("/broadcast test", uid)
        self.assertIn("Admin only", resp)

    async def test_input_length_limit(self):
        uid = BASE_USER_ID + 3
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        await self.send_cmd(self.t("create_card","en"), uid)
        resp = await self.send_cmd("A" * 60, uid)
        self.assertIn("too long", resp.lower())
        self.assertIn("waiting_name", str(await state.get_state()))

    async def test_ready_broadcast(self):
        uid = ADMIN_ID
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid); await state.reset_state()
        resp = await self.send_cmd("/ready_broadcast", uid)
        self.assertIn("NIFTI", resp)
        self.assertIn("51%", resp)

    async def asyncTearDown(self):
        await bot_module.pool.close()

if __name__ == "__main__":
    unittest.main()
