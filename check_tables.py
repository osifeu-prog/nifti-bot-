import asyncpg, asyncio, os

async def q():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"))
    tables = ["products", "purchases", "commissions", "stores", "payment_methods", "invoices", "wallets", "transactions", "coupons"]
    for t in tables:
        try:
            cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1", t)
            if cols:
                print(f"\n=== {t} ===")
                for c in cols:
                    print(f"  {c['column_name']} ({c['data_type']})")
            else:
                print(f"\n=== {t} === (missing)")
        except Exception as e:
            print(f"\n=== {t} === ERROR: {e}")
    await conn.close()

asyncio.run(q())
