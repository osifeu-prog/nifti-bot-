import os

class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()

