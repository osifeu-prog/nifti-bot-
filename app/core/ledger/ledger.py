from app.core.engine import engine

class Ledger:

    @staticmethod
    def add_balance(user_id: int, amount: float):
        engine.execute("""
            UPDATE users
            SET balance = COALESCE(balance, 0) + %s
            WHERE id = %s
        """, (amount, user_id))

    @staticmethod
    def get_balance(user_id: int):
        res = engine.execute("""
            SELECT balance FROM users WHERE id = %s
        """, (user_id,))
        return res[0]["balance"] if res and res[0]["balance"] else 0

    @staticmethod
    def transfer(from_id: int, to_id: int, amount: float):
        engine.execute("""
            UPDATE users SET balance = COALESCE(balance,0) - %s WHERE id = %s
        """, (amount, from_id))

        engine.execute("""
            UPDATE users SET balance = COALESCE(balance,0) + %s WHERE id = %s
        """, (amount, to_id))

