from core.engine import engine

engine.execute("DROP TABLE IF EXISTS users")

engine.execute("""
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

print("DB RESET OK")

