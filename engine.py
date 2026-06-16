import asyncio
import asyncpg
from config import DATABASE_URL

class EngineV21:
    def __init__(self):
        self.pool = None
        self.loop = asyncio.new_event_loop()

    async def _start(self):
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        print("[ENGINE] v2.1 ONLINE")

    def start(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._start())

    async def _execute(self, q, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(q, *args)

    def execute(self, q, *args):
        return self.loop.run_until_complete(self._execute(q, *args))

    async def _close(self):
        if self.pool:
            await self.pool.close()

    def close(self):
        self.loop.run_until_complete(self._close())
        print("[ENGINE] OFF")

engine = EngineV21()

