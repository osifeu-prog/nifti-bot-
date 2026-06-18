import asyncpg, asyncio, os, json
from datetime import datetime

async def backup():
    url = os.getenv('DATABASE_URL', 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main')
    conn = await asyncpg.connect(url)
    
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    dump = {}
    for t in tables:
        name = t['tablename']
        rows = await conn.fetch(f'SELECT * FROM {name}')
        dump[name] = [dict(r) for r in rows]
    
    filename = f"nifti_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dump, f, default=str, ensure_ascii=False, indent=2)
    
    print(f'Backup saved to {filename}')
    await conn.close()

asyncio.run(backup())
