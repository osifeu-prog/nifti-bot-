# 🚀 NIFTI System Architecture - Master Guide

## 1. Vision
NIFTI is an autonomous Web3-integrated Telegram ecosystem providing financial gamification, viral referral loops, and secure asset management.

## 2. User Journey & Tiers
- **Guest (Pre-Signup):** Access to public market, limited preview.
- **Member (Free):** Access to core trading, 4 coins/signup bonus.
- **Investor (Premium 50k+):** Exclusive assets, 9.4 coins/referral-purchase, 0% platform fees.

## 3. Command Suite
### General
- /start  Onboarding & Referral activation.
- /market  Buy digital assets.
- /earnings  Balance overview.
- /referrals  Referral dashboard & link sharing.

### Admin
- /airdrop <amount>  System-wide liquidity injection.
- /stats  Real-time ROI and user growth reporting.
- /broadcast <msg>  Mass message to all users.

## 4. Viral Math
- Signup Bonus: 4 Coins (to referrer).
- Purchase Bonus: 9.4 Coins (to referrer).
- Level 2 Bonus: 2 Coins (to referrer of referrer).

## 5. Technical Stack
- Python 3.10, aiogram 2.25.2, FastAPI, asyncpg, PostgreSQL
- Docker-ready for Railway/VPS deployment
- TON blockchain integration via TonCenter API
