import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL
import time

class Engine:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        while True:
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                self.conn.autocommit = True
                print("[DB] CONNECTED")
                break
            except Exception as e:
                print("[DB ERROR]", e)
                time.sleep(2)

    def execute(self, q, params=None):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(q, params or ())
                try:
                    return cur.fetchall()
                except:
                    return None
        except Exception as e:
            print("[DB ERROR]", e)
            print("[DB RECONNECT]")
            self.connect()
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            print("[DB] CLOSED")

engine = Engine()

