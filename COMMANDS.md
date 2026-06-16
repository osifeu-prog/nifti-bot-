# NIFTI Bot - Command Map
# Generated 06/16/2026 16:08:49

## User Commands
| Command | Description |
|---------|-------------|
| /start | Main menu + referral registration |
| /status | System statistics (users, cards) |
| /market | Browse card marketplace |
| /earnings | View balance and earnings |
| /leaderboard | Top users by referrals |
| /referrals | Your referral link and count |
| /set_price | Set your card price |
| /edit_card | Edit your card name |
| /my_card | View your card |
| /card_image | Generate card PNG image |

## Admin Commands
| Command | Description |
|---------|-------------|
| /admin | Admin panel overview |
| /stats | Detailed system statistics |
| /airdrop | Send coins to all users |
| /broadcast | Send message to all users |
| /diagnostics | System diagnostics report |

## Inline Menu Callbacks
| Callback Data | Action |
|---------------|--------|
| menu_create | Start card creation FSM |
| menu_mycard | Show user card |
| menu_market | Show market |
| menu_earnings | Show earnings |
| menu_leaderboard | Show leaderboard |
| menu_settings | Settings placeholder |
| buy_{id}_{price} | Generate TON payment memo |
