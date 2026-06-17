# NIFTI Master Plan (v4.3 -> v5.0)

## Vision
Full digital business card ecosystem on Telegram: NFTs, shops, token exchange.
9 languages, advanced wallet integration, TON blockchain connectivity.

## Immediate Next Steps
1. **Fix /check DB error** (connection pool release)
2. **Fix Spin prize bug** (ensure users receive points)
3. **Create /plan command** (display this plan)
4. **Wallet System**  full wallet management (balance, deposit, withdraw, TON integration)
5. **NFT Card Minting**  generate card image, upload to IPFS, TON metadata
6. **Franchise Shops**  allow users to open shops, list cards, earn commissions
7. **IWA Exchange**  dynamic exchange rate, burn mechanism
8. **9 Languages**  full i18n (English, Hebrew, Russian, Arabic, Spanish, French, German, Portuguese, Japanese)
9. **Landing Page**  web page for card viewing, leaderboard, market
10. **TON Connect**  wallet integration for seamless purchases

## Wallet Spec
- /wallet  show balance, deposit address
- /deposit  generate TON address with memo
- /withdraw  send TON to external address
- /transactions  list recent transactions
- TON Scanner detects incoming payments and updates balance

## NFT Card Spec
- /mint  generate PNG card, upload to IPFS, return URL
- Card metadata: name, profession, level, price, photo
- TON NFT metadata standard

## Exchange Spec
- /exchange <iwa_amount>  convert IWA to TON
- Admin-controlled rate + burn percent
- Transaction history

## i18n Spec
- 9 languages in lang.json
- Dynamic language selection (/language)
- All commands/buttons translated

## Marketing Funnel
- Landing page at https://bot-production-c2a5.up.railway.app
- QR codes for each card
- Referral tracking in DB

## Decisions Log
- MemoryStorage for FSM (no Redis until scaling)
- PowerShell blocks for all deployment
- All plans stored in MASTER_PLAN.md
- Each new AI session reads MASTER_PLAN.md first
