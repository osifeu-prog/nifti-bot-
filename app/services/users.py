from app.core.engine import engine

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
        res = engine.execute("""
            SELECT * FROM users WHERE id = %s
        """, (user_id,))
        return res[0] if res else None

