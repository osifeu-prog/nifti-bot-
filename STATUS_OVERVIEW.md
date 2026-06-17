# 📊 NIFTI SYSTEM STATUS OVERVIEW
**Last Update:** 2026-06-17 18:50
**Version:** v5.3.6 (Stable)

## 🏗️ Architecture
- Bot: aiogram 2.25.2 (Webhook)
- API: FastAPI + Uvicorn
- DB: PostgreSQL (asyncpg)
- Deploy: Railway (auto-deploy from GitHub)

## ✅ Implemented & Working
| Feature | Status | Command/Handler |
|---------|--------|-----------------|
| Glass Dashboard | ✅ | /start |
| Card Creation (FSM) | ✅ | Create Card button |
| Edit Wizard | ✅ | ✏️ Edit button |
| My Card | ✅ | /my_card |
| Market (Carousel) | ✅ | /market (10 demo cards) |
| Wallet | ✅ | /wallet |
| Leaderboard | ✅ | /leaderboard |
| Earnings | ✅ | /earnings |
| Invite + QR | ✅ | /invite |
| Spin Casino | ✅ | /spin (39% win) |
| Admin Panel | ✅ | /admin |
| Dev Panel | ✅ | /dev |
| Healthcheck | ✅ | /healthcheck |
| System Check | ✅ | /check |
| Analytics | ✅ | /stats, /analytics |
| Demo Mode | ✅ | /demo |
| Community Verify | ✅ | /verify |
| TON Scanner | ✅ | Background |
| Referral System | ✅ | TON + IWA |
| Rate Limiting | ✅ | 1 req/sec |
| Audit Log | ✅ | admin_logs table |
| State Machine | ✅ | state column |
| Auto Tests | ✅ | test_all.ps1 |

## 🚧 In Progress / Known Issues
- **Edit Wizard buttons**  Fixed in v5.3.6 (startswith filter)
- **Architecture/Roadmap docs**  Missing files (need regeneration)
- **Market demo cards**  Populated via /seed_market

## 📋 Next Steps (Priority Order)
1. **Stabilize Edit Wizard**  Ensure all buttons respond
2. **Regenerate docs files**  architecture.md, roadmap.md
3. **Onboarding Flow**  Welcome GIF/tutorial
4. **NFT Card Generation**  /mint with Pillow
5. **Order Book / Exchange**  Trading system
6. **9 Languages**  Full i18n

## 🔗 Key Files
- `MASTER_PLAN.md`  Vision & roadmap
- `NIFTI_SCHEMA.json`  Data schema
- `SYSTEM_COMMAND.md`  SSoT protocol
- `AUDIT_PROMPT.md`  Audit template
- `test_all.ps1`  Auto tests
- `server.py`  Main bot code

## 🔒 Protocol
- Every new session starts by reading STATUS_OVERVIEW.md
- All changes documented in MASTER_PLAN.md
- PowerShell blocks for deployment
- No new features until current phase is stable
