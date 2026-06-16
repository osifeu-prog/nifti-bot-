import time
from collections import defaultdict
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

class RateLimiterMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    def __init__(self, max_requests=5, window=10):
        super().__init__()
        self.max_requests = max_requests
        self.window = window
        self.users = defaultdict(list)

    async def pre_process(self, obj, data, *args):
        from aiogram.types import Message
        if isinstance(obj, Message):
            user_id = obj.from_user.id
            now = time.time()
            self.users[user_id] = [t for t in self.users[user_id] if now - t < self.window]
            if len(self.users[user_id]) >= self.max_requests:
                await obj.answer("⏳ You are sending too many requests. Please wait.")
                return False
            self.users[user_id].append(now)
        return True
