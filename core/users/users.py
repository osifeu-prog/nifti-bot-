from core.db.database import execute

class Users:

    @staticmethod
    def get_or_create(user_id: int, username: str = None):
        res = execute("SELECT * FROM users WHERE id = %s", (user_id,))
        if res:
            return res[0]

        execute(
            "INSERT INTO users (id, username, balance) VALUES (%s, %s, 0)",
            (user_id, username)
        )
        return {"id": user_id, "balance": 0}

