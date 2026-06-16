from db.engine import engine

engine.execute("""
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

print("[DB] READY V4")

