$TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$BASE = "https://bot-production-c2a5.up.railway.app"

Write-Host "=== System Check ===" -ForegroundColor Cyan

Write-Host "`n1. Webhook Status:" -ForegroundColor Yellow
$web = Invoke-RestMethod -Uri "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
Write-Host "   URL: $($web.result.url)" -ForegroundColor Green
Write-Host "   Pending: $($web.result.pending_update_count)" -ForegroundColor Green

Write-Host "`n2. API Root:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$BASE/" | ConvertTo-Json

Write-Host "`n3. Admin Page:" -ForegroundColor Yellow
$code = Invoke-WebRequest -Uri "$BASE/admin" -UseBasicParsing | Select-Object -ExpandProperty StatusCode
Write-Host "   Status: $code" -ForegroundColor $(if ($code -eq 200) {'Green'} else {'Red'})

Write-Host "`n4. Railway Status:" -ForegroundColor Yellow
railway status

Write-Host "`n5. Last Logs:" -ForegroundColor Yellow
railway logs --tail 5

Write-Host "`n✅ Check complete. Run again anytime with: .\check_system.ps1" -ForegroundColor Green
