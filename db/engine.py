import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

class EngineV4:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = True

    def execute(self, q, params=None):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params or ())
            try:
                return cur.fetchall()
            except:
                return None

    def close(self):
        self.conn.close()
        print("[ENGINE] CLOSED")

engine = EngineV4()

