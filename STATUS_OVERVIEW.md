# NIFTI STATUS - 2026-06-18

## Working
- Bot: LIVE at https://bot-production-c2a5.up.railway.app
- DB: 23 tables, PostgreSQL Railway
- Handlers: start, market (demo), leaderboard, admin, earnings, invite, spin
- TON Scanner: running every 600s
- BOM/null bytes: fixed in server.py + marketplace.py

## Fixed Today
- server.py BOM removed
- marketplace.py created (clean)
- requirements.txt updated
- DB columns added

## Known Issues
- Emoji broken in some deploys (PYTHONIOENCODING missing on Railway)
- /market shows demo cards (needs real products)
- /buy, /store, /addproduct not connected to real DB
- Mini App: User ID not found (frontend fix needed)
- /db_backup returns empty
- /dev panel broken

## Next Session
1. Set PYTHONIOENCODING on Railway
2. Replace /market handler with real products
3. Fix Mini App user_id