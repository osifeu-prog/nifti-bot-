import asyncio, json, os, asyncpg, sys, logging, unittest
from unittest.mock import AsyncMock, patch
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
        self.bot = bot
        self.dp = bot_module.dp
        self.dp.bot = self.bot
        self.dp.storage = MemoryStorage()
        Dispatcher.set_current(self.dp)
        Bot.set_current(self.bot)

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

        bot_module.pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"));
        async with bot_module.pool.acquire() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)");
            await conn.execute("CREATE TABLE IF NOT EXISTS promo_claims (user_id BIGINT, wallet TEXT, claimed_at TIMESTAMPTZ DEFAULT NOW())
        await conn.execute('''CREATE TABLE IF NOT EXISTS wallets (user_id BIGINT PRIMARY KEY, address TEXT NOT NULL, verified BOOLEAN DEFAULT FALSE, connected_at TIMESTAMPTZ DEFAULT NOW())''')");
            await conn.execute("INSERT INTO settings (key, value) VALUES ('free_cards_max', '200'), ('free_cards_claimed', '0') ON CONFLICT (key) DO NOTHING")
        bot_module.load_lang()
        bot_module.ADMIN_ID = BASE_USER_ID

    async def mock_send_message(self, chat_id, text, **kwargs):
        msg = Message()
        msg.text = text
        msg.chat = Chat(id=chat_id, type='private')
        msg.from_user = User(id=999, is_bot=True, first_name="Bot")
        self.sent_messages.append(msg)
        return msg

    def make_msg(self, text, user_id):
        msg = Message()
        msg.text = text
        msg.chat = Chat(id=user_id, type='private')
        msg.from_user = User(id=user_id, is_bot=False, first_name="Test")
        return msg

    async def send_cmd(self, cmd, user_id):
        self.sent_messages.clear()
        msg = self.make_msg(cmd, user_id)
        update = types.Update(update_id=1, message=msg)
        await self.dp.process_update(update)
        if self.sent_messages:
            return self.sent_messages[-1].text
        return ""

    def t(self, key, lang):
        LANG = bot_module.LANG
        return LANG.get(lang, LANG['en']).get(key, LANG['en'].get(key, key))

    langs_codes = ['en','he','ru','ar','fr','es','zh','pt']

    async def test_all_languages(self):
        for idx, code in enumerate(self.langs_codes):
            uid = BASE_USER_ID + idx
            with self.subTest(lang=code):
                async with bot_module.pool.acquire() as conn:
                    await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
                    await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, $2)", uid, code)

                state = self.dp.current_state(chat=uid, user=uid)
                await state.reset_state()

                # --- Market ---
                market_resp = await self.send_cmd("/market", uid)
                self.assertIn(self.t('market', code).split('{sellers}')[0][:20], market_resp)
                self.assertIn('/setprice', market_resp)

                # --- Setprice ---
                exp = self.t('setprice_done', code).format(price="5.0")
                self.assertIn(exp, await self.send_cmd("/setprice 5", uid))
                exp2 = self.t('setprice_prompt', code).format(price="5.0")
                self.assertIn(exp2, await self.send_cmd("/setprice", uid))

                # --- Simple commands ---
                self.assertIn(self.t('guide', code)[:10], await self.send_cmd("/guide", uid))
                self.assertIn(self.t('feedback_sent', code)[:10], await self.send_cmd("/feedback test", uid))

                # --- Referrals ---
                ref_exp = self.t('myreferrals', code).format(refs=0, pts=0)
                self.assertIn(ref_exp, await self.send_cmd("/myreferrals", uid))

                # --- Status (header only) ---
                status_header = self.t('status', code).split('{users}')[0]
                self.assertIn(status_header, await self.send_cmd("/status", uid))

                # ====== CARD CREATION  direct handler calls ======
                msg = self.make_msg("dummy", uid)
                state_mock = AsyncMock()
                state_mock.get_data.return_value = {'lang': code}

                await bot_module.process_name(msg, state_mock)
                last = self.sent_messages[-1].text
                self.assertIn(self.t('card_prof', code)[:10], last)

                await bot_module.process_prof(msg, state_mock)
                last = self.sent_messages[-1].text
                self.assertIn(self.t('card_wallet', code)[:10], last)

                state_mock.get_data.return_value = {'lang': code, 'name': 'Osif', 'prof': 'Architect'}
                await bot_module.process_wallet(msg, state_mock)
                last = self.sent_messages[-1].text
                self.assertIn(self.t('card_done', code).split('{')[0].strip(), last)

        # --- Admin commands ---
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", BASE_USER_ID)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", BASE_USER_ID)
        state = self.dp.current_state(chat=BASE_USER_ID, user=BASE_USER_ID)
        await state.reset_state()
        self.assertIn("All Bot Commands", await self.send_cmd("/commands", BASE_USER_ID))

    async def test_new_features(self):
        # Test /testsuite (admin)
        uid = BASE_USER_ID
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid)
        await state.reset_state()
        resp = await self.send_cmd("/testsuite", uid)
        self.assertIn("All 8 languages", resp)

        # Test /claim with valid code
        uid2 = BASE_USER_ID + 100
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=$1", uid2)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES ($1, 'en')", uid2)
        state2 = self.dp.current_state(chat=uid2, user=uid2)
        await state2.reset_state()
        resp = await self.send_cmd("/claim NIFTI200", uid2)
        self.assertTrue(resp)

        # Test /simulate_purchase
        resp = await self.send_cmd("/simulate_purchase 10 123456", uid)
        self.assertIn("Platform fee (20%): 2.0 TON", resp)
        self.assertIn("Seller receives: 8.0 TON", resp)


    async def test_ton_connect(self):
        uid = BASE_USER_ID
        async with bot_module.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id=    async def asyncTearDown", uid)
            await conn.execute("INSERT INTO users (user_id, lang) VALUES (    async def asyncTearDown, 'en')", uid)
        state = self.dp.current_state(chat=uid, user=uid)
        await state.reset_state()

        # Test /connect (should return guide)
        resp = await self.send_cmd("/connect", uid)
        self.assertIn("Connect Your TON Wallet", resp)

        # Test /wallet with valid address
        resp = await self.send_cmd("/wallet UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp", uid)
        self.assertIn("Wallet connected!", resp)

        # Test /wallet with invalid address
        resp = await self.send_cmd("/wallet invalid", uid)
        self.assertIn("Invalid TON address", resp)

    async def asyncTearDown(self):
        await bot_module.pool.close()

if __name__ == "__main__":
    unittest.main()



