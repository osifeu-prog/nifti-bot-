import psycopg2
import os

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    balance NUMERIC DEFAULT 0
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ledger (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    amount NUMERIC,
    type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

print("[DB] CLEAN SCHEMA READY")

cur.close()
conn.close()
