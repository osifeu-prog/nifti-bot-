import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger("NIFTI_AUDIT")
logger.setLevel(logging.INFO)

class SystemAudit:
    @staticmethod
    async def check_db_health(pool):
        try:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"CRITICAL: DB Health Check Failed: {e}")
            return False

    @staticmethod
    def log_event(event_name: str, user_id: int, data: dict = None):
        timestamp = datetime.now().isoformat()
        log_entry = f"[AUDIT] {timestamp} | Event: {event_name} | User: {user_id} | Data: {data or {}}"
        logger.info(log_entry)

def log_execution(event_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            msg = None
            for a in args:
                if hasattr(a, 'from_user'):
                    msg = a
                    break
            user_id = msg.from_user.id if msg else 'unknown'
            SystemAudit.log_event(event_name, user_id)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
