# PROJECT_MASTER  NIFTI

## Vision
NIFTI is a Telegram Mini App + Bot that gives every user a digital business card (NFT-like). Users can showcase their profession, receive payments via TON, and participate in a referral/social marketplace.

## Core Features (v1.5)
- Telegram Bot (/start, /my_card, /market, /wallet, etc.)
- Mini App (React SPA) served at /mini-app
- Digital card with name, profession, wallet
- TON payment QR + deep link
- SIF Token (in-app currency)
- Marketplace with Buy button (20% fee)
- Admin Dashboard (Jinja2)
- BOC Verification (TON Center API)

## Tech Stack
- Backend: Python (FastAPI + aiogram)
- Frontend: React (Vite) → served as static files
- Database: PostgreSQL (asyncpg)
- Hosting: Railway (bot, PostgreSQL, Redis)
- Blockchain: TON (payments, scanning)

## Active Endpoints
- GET /api/card/{user_id}
- GET /api/qr/{user_id}
- GET /mini-app (SPA)
- POST /webhook (Telegram)

## Environment Variables (set in Railway)
- BOT_TOKEN
- ADMIN_USER_ID
- TON_WALLET
- DATABASE_URL
- REDIS_URL

## Repository
D:\NIFTI
GitHub: osifeu-prog/nifti-bot-
