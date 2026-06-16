from core.db.engine import engine

class Ledger:

    @staticmethod
    def get_balance(user_id):
        res = engine.execute(
            "SELECT balance FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )

        if not res:
            return 0

        return res[0]["balance"]
