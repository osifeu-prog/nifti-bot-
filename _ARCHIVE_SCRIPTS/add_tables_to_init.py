# add_tables_to_init.py
server_path = r"D:\NIFTI\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

# SQL to add right after "CREATE TABLE IF NOT EXISTS analytics"
new_tables = '''
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY, name TEXT, description TEXT, price REAL, active BOOLEAN DEFAULT TRUE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id SERIAL PRIMARY KEY, user_id BIGINT, store_name TEXT, description TEXT, created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id BIGSERIAL PRIMARY KEY, buyer_user_id BIGINT, product_id INTEGER, referrer_user_id BIGINT, amount_ton NUMERIC, commission_paid BOOLEAN DEFAULT FALSE, tx_hash TEXT, invoice_id TEXT, status TEXT DEFAULT \'pending\', created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY, user_id BIGINT, amount DOUBLE PRECISION, type VARCHAR(50), timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS commissions (
                id BIGSERIAL PRIMARY KEY, from_user_id BIGINT, to_user_id BIGINT, amount_ton NUMERIC, level INTEGER, status TEXT DEFAULT \'pending\', purchase_id BIGINT, created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS xp (
                user_id BIGINT PRIMARY KEY, xp INTEGER DEFAULT 0, badge TEXT
            )
        """)
'''

# Find the line after the last CREATE TABLE in init_db
marker = 'INSERT INTO casino_settings'
insert_pos = content.find(marker)
if insert_pos == -1:
    marker = 'for col, typ in'
    insert_pos = content.find(marker)

content = content[:insert_pos] + new_tables + '\n        ' + content[insert_pos:]

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Tables added to init_db")
