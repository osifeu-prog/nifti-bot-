from app.core.engine import engine

def run_tests():
    print("[TEST] ENGINE TEST")
    res = engine.execute("SELECT 1")
    print("[TEST] DB OK:", res)

    print("[TEST] USERS TABLE CHECK")
    engine.execute("SELECT * FROM users LIMIT 1")

    print("[TEST] ALL OK")

if __name__ == "__main__":
    run_tests()

