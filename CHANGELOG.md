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
## [v1.5.1] - 2026-06-19
### Fixed
- Removed dd_utf8_header middleware that forced Content-Type: application/json on all responses, breaking JS delivery.
- Mini App now correctly serves JavaScript with pplication/javascript MIME type.
### Known issues
- Browser caching may still serve stale content; resolved by using fresh profiles / hard refresh.
## [v1.5.2] - 2026-06-19
### Fixed
- Cache busting for Mini App  added ?v= timestamp to JS src, plus Cache-Control headers.
- MIME type collision (utf8 middleware removed).
### Added
- Source of Truth: PROJECT_MASTER.md, docs/vision.md, docs/roadmap.md, docs/known_bugs.md, docs/decisions.md
