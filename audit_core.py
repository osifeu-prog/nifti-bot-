import logging

class SystemAudit:
    @staticmethod
    async def check_db_health(pool):
        try:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"DB Health Check Failed: {e}")
            return False

    @staticmethod
    def log_event(event_name, user_id, data=None):
        logging.info(f"[AUDIT] {event_name} | User: {user_id} | Data: {data}")
