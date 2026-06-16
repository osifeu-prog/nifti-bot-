from app.core.engine import engine

class Referral:

    @staticmethod
    def add_referral(user_id: int, ref_id: int):
        engine.execute("""
            UPDATE users
            SET ref_id = %s
            WHERE id = %s
        """, (ref_id, user_id))

    @staticmethod
    def count_referrals(user_id: int):
        res = engine.execute("""
            SELECT COUNT(*) as c FROM users WHERE ref_id = %s
        """, (user_id,))
        return res[0]["c"] if res else 0

