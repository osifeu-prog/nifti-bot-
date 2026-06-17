# NIFTI UI/UX Manifesto (v1.0)

## Visual Language
- All headers in bold, use horizontal rules for separation.
- Emojis for key actions (💳 Card, 🛒 Market, 📈 Earnings).
- Inline keyboards for navigation, no text commands for main flow.

## Edit Card Wizard (State Machine)
- User clicks "Edit Card" → inline keyboard: [Name] [Profession] [Price] [Photo]
- When editing, bot locks user into that state until completion or cancel.
- State machine prevents /start from interrupting the flow.

## Command Separation
- **Regular Admins** can use: /admin, /stats, /broadcast, /airdrop, /set_edge
- **Super Admins (you)** can use: /dev (menu for /db_setup, /grant_admin, /healthcheck, /check, /docs, /plan)
- Regular users see only user commands.

## Error Handling
- If input invalid, show ❌ with explanation and offer "Back" button.
- Never leave user without a clear next step.
