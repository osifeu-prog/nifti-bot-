import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.engine import engine

def test_db():
    print("[TEST] DB CONNECTION TEST...")
    engine.execute("SELECT 1")
    print("[TEST] OK")

if __name__ == "__main__":
    test_db()

