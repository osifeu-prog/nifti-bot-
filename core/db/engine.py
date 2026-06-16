import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool


class SafePoolEngine:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_URL")
        self.pool = None
        self.connect()

    def connect(self):
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                dsn=self.dsn
            )
            print("[DB] Pool Connected")
        except Exception as e:
            print("[DB CONNECT FAIL]", e)
            self.pool = None

    def execute(self, query, params=None, fetch=False):
        if not self.pool:
            self.connect()
            if not self.pool:
                raise Exception("DB UNAVAILABLE")

        conn = self.pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())

            if fetch or query.strip().lower().startswith("select"):
                return cur.fetchall()

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print("[DB ERROR]", e)
            raise

        finally:
            cur.close()
            self.pool.putconn(conn)


engine = SafePoolEngine()