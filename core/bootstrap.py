import os
from core.db.init_db import init_db

def bootstrap():
    print("[BOOTSTRAP] ZERO-CRASH MODE START")

    required = ["DATABASE_URL", "BOT_TOKEN"]
    missing = [x for x in required if not os.getenv(x)]

    if missing:
        print("[BOOTSTRAP WARNING]", missing)

    try:
        init_db()
    except Exception as e:
        print("[BOOTSTRAP SAFE ERROR]", e)

    print("[BOOTSTRAP] SYSTEM READY")

if __name__ == "__main__":
    bootstrap()
