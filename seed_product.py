import os, asyncio, asyncpg

async def main():
    url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(url)
    await conn.execute(
        "INSERT INTO products (name, description, price) VALUES ($1, $2, $3)",
        "SIF Token Sample", "A demonstration product for the marketplace", 5.0
    )
    # Also create a store for the admin user
    await conn.execute(
        "INSERT INTO stores (user_id, store_name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        224223270, "SIF Token Sample"
    )
    await conn.close()
    print("Demo product added.")
asyncio.run(main())
