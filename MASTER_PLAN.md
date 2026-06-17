# NIFTI Master Plan (v4.3.1 → v5.0)

## Vision
Full digital business card ecosystem on Telegram: NFTs, shops, token exchange.
9 languages, advanced wallet integration, TON blockchain connectivity.

## Immediate Next Steps
1. **Fix /check DB error** ✅
2. **Fix Spin prize bug** ✅
3. **/plan command** ✅
4. **Wallet System**  /wallet, /deposit, /withdraw, /transactions
5. **NFT Card Minting**  /mint, IPFS, TON metadata
6. **Franchise Shops**  /openshop, /sell, commissions
7. **IWA Exchange**  /exchange, dynamic rate, burn
8. **9 Languages**  full i18n (en, he, ru, ar, es, fr, de, pt, ja)
9. **Landing Page**  card viewer, leaderboard, market
10. **TON Connect**  wallet integration

## Wallet Spec
- /wallet  show balance, deposit address
- /deposit  generate TON address with memo
- /withdraw  send TON to external address
- /transactions  list recent transactions

## NFT Card Spec
- /mint  generate PNG card, upload to IPFS
- Card metadata: name, profession, level, price, photo

## Exchange Spec
- /exchange <iwa> → convert to TON
- Admin rate + burn, transaction history

## i18n Spec
- 9 languages in lang.json
- /language  switch language
- All UI translated

## Marketing Funnel
- Landing page at https://bot-production-c2a5.up.railway.app
- QR codes for each card
- Referral tracking in DB

## Decisions Log
- MemoryStorage for FSM (no Redis until scaling)
- PowerShell blocks for deployment
- MASTER_PLAN.md is the single source of truth
- Every new AI session starts by reading MASTER_PLAN.md
