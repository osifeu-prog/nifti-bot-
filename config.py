import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

def load_env():
    if not ENV_FILE.exists():
        raise RuntimeError(".env missing")

    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

load_env()

def must(key: str):
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing env: {key}")
    return val

DATABASE_URL = must("DATABASE_URL")
BOT_TOKEN = must("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

print("[CONFIG] OK")

