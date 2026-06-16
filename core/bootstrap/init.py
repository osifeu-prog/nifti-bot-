import os
from core.db.engine import engine

def init_core():
    print("[CORE] BOOTSTRAP START")

    # DB health check
    engine.execute("SELECT 1")

    print("[CORE] DB OK")
    print("[CORE] READY FOR SERVICES")

if __name__ == "__main__":
    init_core()

