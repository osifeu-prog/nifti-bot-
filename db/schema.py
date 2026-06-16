from core.engine import engine

def init_db():
    engine.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    print("[DB] READY V6")

