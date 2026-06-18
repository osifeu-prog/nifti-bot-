# Changelog  NIFTI Bot

## v1.4.0  Mini App Static Serving & API Fixes (2026-06-18)

### Added
- **Mini App static serving**  React build served from /mini-app with SPA fallback.
- **API endpoint GET /api/card/{user_id}**  returns JSON with card_name, card_prof, wallet.
- Admin Dashboard integrated (Jinja2).
- Session Protocol documented (SESSION_PROTOCOL.md).

### Fixed
- **SQL syntax error** in /api/card  missing $1 placeholder causing 500 errors.
- Null bytes cleaned from server.py.
- .gitignore updated to allow rontend/dist in Railway.
- Vite build Node.js version upgraded to 22 (was 18, incompatible).
- Duplicate code removed (old mount, catch‑all route dead code).
- Various file cleanups and archiving.

### Known Issues
- mini-app React code requires user_id query parameter; Telegram WebApp integration pending.
- Some routes defined after uvicorn.run still exist but never executed (harmless).

### Upcoming
- TON payment QR / deep link generation.
- Landing page, Full i18n, NFT card generation, Order book.
