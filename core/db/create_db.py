import psycopg2

ADMIN_DB_URL = "postgresql://postgres:1234@localhost:5432/postgres"
TARGET_DB = "nifti"

def create_database():
    conn = psycopg2.connect(ADMIN_DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}'")
    exists = cur.fetchone()

    if not exists:
        print("[DB] Creating database nifti...")
        cur.execute(f"CREATE DATABASE {TARGET_DB}")
    else:
        print("[DB] Database already exists")

    cur.close()
    conn.close()

if __name__ == "__main__":
    create_database()

