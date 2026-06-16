from app.core.engine import engine

class SystemService:

    @staticmethod
    def health_check():
        return engine.execute("SELECT 1")


class UserService:

    @staticmethod
    def create_user(user_id, username):
        return engine.execute("""
            INSERT INTO users (id, username)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (user_id, username))

    @staticmethod
    def get_user(user_id):
        res = engine.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return res[0] if res else None

    @staticmethod
    def count_users():
        res = engine.execute("SELECT COUNT(*) as c FROM users")
        return res[0]["c"] if res else 0

