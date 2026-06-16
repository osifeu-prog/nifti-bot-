import asyncio
from engine import engine

class Runtime:
    def __init__(self):
        self.running = False

    async def start(self):
        print("[RUNTIME] STARTING...")
        await engine.start()
        self.running = True
        print("[RUNTIME] ONLINE")

    async def stop(self):
        print("[RUNTIME] STOPPING...")
        await engine.close()
        self.running = False
        print("[RUNTIME] OFF")

runtime = Runtime()

