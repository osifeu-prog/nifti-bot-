# NIFTI Master Plan (v4.4 → v5.0)

## Vision
Full digital business card ecosystem on Telegram: NFTs, shops, token exchange.
9 languages, advanced wallet integration, TON blockchain connectivity.

## Current Phase: Wallet System (v4.4.1)
- /wallet  show balance, deposit address, recent transactions
- /set_wallet <address>  set your TON wallet address
- /deposit  generate memo and address for depositing TON
- /withdraw <amount>  request withdrawal (manual, for now)
- /transactions  list payment history
- TON Scanner automatically detects incoming payments and updates balance/premium status

## Next Steps
4. **NFT Card Minting**  /mint, IPFS, TON metadata
5. **Franchise Shops**  /openshop, /sell, commissions
6. **IWA Exchange**  /exchange, dynamic rate, burn
7. **9 Languages**  full i18n
8. **Landing Page**  card viewer, leaderboard, market
9. **TON Connect**  wallet integration

## Wallet Spec
- /wallet  inline keyboard with options: [Deposit] [Withdraw] [Transactions]
- /set_wallet  save user's TON address (for future use)
- /deposit  sends message: "Send TON to UQCr7... with memo NIFTI_PAY:user_id_xxxxx"
- /transactions  shows last 10 premium_users entries for user
- TON Scanner updates is_premium and balance on detection

## Decisions Log
- MemoryStorage for FSM (no Redis until scaling)
- PowerShell blocks for all deployment
- MASTER_PLAN.md is the single source of truth
- Every new AI session starts by reading MASTER_PLAN.md
