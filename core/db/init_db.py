from core.db.engine import engine

def init_db():
    print("[DB] INIT SCHEMA")

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

    print("[DB] SCHEMA READY")
