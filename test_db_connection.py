import asyncio
import asyncpg
import os

async def test_db():
    dsn = os.getenv('DATABASE_URL')
    print(f"Testing connection to: {dsn}")
    
    try:
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
        print("✅ Pool created successfully")
        
        async with pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            print(f"✅ Connected! PostgreSQL version: {version}")
            
            # בדיקת הטבלאות הרלוונטיות
            tables = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            print(f"✅ Found {tables} tables in public schema")
            
            # בדיקת טבלת users
            users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            print(f"✅ users table exists, count = {users_count}")
            
        await pool.close()
        print("✅ All tests passed - Database is ready for async use")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
