from app.core.engine import engine

def init_db():
    print("[DB] SAFE INIT START")

    engine.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            balance FLOAT DEFAULT 0,
            ref_id BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    print("[DB] SAFE INIT COMPLETE")

