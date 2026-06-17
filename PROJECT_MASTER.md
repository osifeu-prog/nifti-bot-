# NIFTI  Project Master
Version: 4.0 (Stable Diamond)
Last Update: 2026-06-17

## Vision
Create a viral Telegram bot that issues digital business cards (NFT-like),
a marketplace of cards, and a token-based economy (IWA, points, TON).
Users join, create a card, share a referral link, earn TON + IWA,
play a slot machine, and climb a leaderboard.
Future: franchise shops, token exchange, advanced Web3 integration.

## Architecture
- **Bot:** aiogram 2.25.2 (Telegram)
- **Web Framework:** FastAPI (health, webhook, admin page)
- **DB:** PostgreSQL (via asyncpg, pool in nifti_core)
- **Storage:** MemoryStorage for FSM (Redis ready for future)
- **Deploy:** Railway (Dockerfile, GitHub auto-deploy)
- **Public URL:** https://bot-production-c2a5.up.railway.app
- **Admin:** Osif Ungar (user_id 224223270, role admin)

## Core Features (implemented)
- Dynamic menu (hides Create Card if user has one)
- Card creation (name, profession, wallet)
- Edit card (name, profession, photo)
- Profile photo upload and display
- Referral system (TON reward + IWA bonus)
- QR code invite link
- Slot machine with admin-controlled house edge
- Leaderboard, Market (buy/sell cards placeholder)
- Admin panel, Stats, Broadcast, Airdrop
- Healthcheck, System Check (admin commands)
- Rate limiting (in-memory)
- Multi-language support (lang.json  English, Hebrew)

## Databases & Tables
- **users**  main user data, role, points, iwa_balance, photo
- **referrals**  referrer relationships
- **premium_users**  TON payment records
- **casino_settings**  house_edge
- **admin_logs**  audit trail

## Roadmap (next 90 days)
1. **Stability & Documentation** (current)
   - PROJECT_MASTER.md, /docs command, check_system.ps1
   - Fix any missing lang keys (card_created, profile_text)
2. **Onboarding Flow**
   - Welcome message with language choice
   - Tutorial /guide command
3. **NFT Card Features**
   - Generate card image with user data
   - Mint as NFT (TON blockchain)  optional
   - Card templates / themes
4. **Shops & Franchise**
   - Allow users to open a "shop" (list of cards)
   - Affiliate commissions on shop sales
5. **Token Exchange**
   - Exchange IWA points for TON (admin-controlled rate)
   - Burn mechanism for deflation
6. **Web App**
   - Full card viewer at /card/{id}
   - Leaderboard, market on web
7. **Analytics**
   - User growth, activity, revenue dashboard

## Key Decisions
- **No Redis for now**  MemoryStorage is stable; add Redis only when scaling.
- **lang.json** is the translation master file.
- **Admin role** stored in DB; only superadmin can grant admin.
- **All code changes via PowerShell blocks**  avoid manual editing.
- **Use PROJECT_MASTER.md + /docs for AI context**  prevents context loss.

## Contact
- Bot: @NFTY_madness_bot
- Admin: Osif Ungar
