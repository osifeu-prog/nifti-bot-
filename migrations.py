from core.db.engine import engine

def migrate():
    print("[MIGRATIONS] START")

    engine.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        balance NUMERIC DEFAULT 0
    )
    """)

    engine.execute("""
    CREATE TABLE IF NOT EXISTS ledger (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount NUMERIC,
        type TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    print("[MIGRATIONS] DONE")


if __name__ == "__main__":
    migrate()