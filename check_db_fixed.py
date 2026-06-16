import asyncio
import os
import asyncpg

async def check():
    db_url = os.getenv('DATABASE_URL')
    print(f'🔌 Connecting to: {db_url}')
    
    try:
        conn = await asyncpg.connect(db_url)
        print('✅ DB Connection: SUCCESS')
        
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        print(f'\n📋 Found {len(tables)} tables:')
        
        for t in tables:
            table = t['tablename']
            print(f'   • {table}')
            
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
                print(f'     Rows: {count}')
                
                col_count = await conn.fetchval("SELECT COUNT(*) FROM information_schema.columns WHERE table_name=", table)
                print(f'     Columns: {col_count}')
            except Exception as e:
                print(f'     Error reading table: {e}')
        
        await conn.close()
        print('\n✅ Full DB Check Completed!')
        
    except Exception as e:
        print(f'❌ DB Error: {type(e).__name__} - {e}')

asyncio.run(check())
