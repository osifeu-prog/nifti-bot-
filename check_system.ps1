$TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$BASE = "https://bot-production-c2a5.up.railway.app"

Write-Host "=== NIFTI System Check ===" -ForegroundColor Cyan

# 1. Webhook
Write-Host "`n1. Webhook Status:" -ForegroundColor Yellow
$web = Invoke-RestMethod -Uri "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
Write-Host "   URL: $($web.result.url)" -ForegroundColor Green
Write-Host "   Pending: $($web.result.pending_update_count)" -ForegroundColor $(if ($web.result.pending_update_count -eq 0) {'Green'} else {'Yellow'})
if ($web.result.last_error_message) {
    Write-Host "   Last Error: $($web.result.last_error_message)" -ForegroundColor Red
} else {
    Write-Host "   No recent errors." -ForegroundColor Green
}

# 2. API
Write-Host "`n2. API Root:" -ForegroundColor Yellow
try {
    $api = Invoke-RestMethod -Uri "$BASE/"
    Write-Host "   Response: $($api.status)" -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
}

# 3. Admin Page
Write-Host "`n3. Admin Page:" -ForegroundColor Yellow
try {
    $code = Invoke-WebRequest -Uri "$BASE/admin" -UseBasicParsing -TimeoutSec 10 | Select-Object -ExpandProperty StatusCode
    Write-Host "   HTTP $code" -ForegroundColor $(if ($code -eq 200) {'Green'} else {'Red'})
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
}

# 4. Card Page
Write-Host "`n4. Card Page (ID 224223270):" -ForegroundColor Yellow
try {
    $card = Invoke-WebRequest -Uri "$BASE/card/224223270" -UseBasicParsing -TimeoutSec 10
    Write-Host "   HTTP $($card.StatusCode)" -ForegroundColor $(if ($card.StatusCode -eq 200) {'Green'} else {'Red'})
} catch {
    Write-Host "   FAILED: $_" -ForegroundColor Red
}

# 5. Railway Status
Write-Host "`n5. Railway Status:" -ForegroundColor Yellow
railway status

# 6. Recent Logs
Write-Host "`n6. Recent Logs (last 5):" -ForegroundColor Yellow
railway logs --tail 5

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Run this anytime with: .\check_system.ps1" -ForegroundColor Cyan
