$TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$BASE = "https://bot-production-c2a5.up.railway.app"

Write-Host "=== NIFTI Auto Test v5.1 ===" -ForegroundColor Cyan

# Webhook
Write-Host "`n[Webhook]" -ForegroundColor Yellow
$web = Invoke-RestMethod "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
Write-Host "  URL: $($web.result.url)" -ForegroundColor Green
Write-Host "  Pending: $($web.result.pending_update_count)" -ForegroundColor $(if($web.result.pending_update_count -eq 0){'Green'}else{'Yellow'})

# Simulate commands
$cmds = @("/start", "/my_card", "/leaderboard", "/earnings", "/spin", "/invite", "/status", "/docs", "/news", "/commands", "/wallet", "/dev", "/admin", "/stats", "/healthcheck", "/check", "/verify", "/roadmap", "/architecture")
foreach ($c in $cmds) {
    Write-Host "`n[Sim] $c" -ForegroundColor Yellow
    $body = "{`"update_id`":1,`"message`":{`"message_id`":1,`"from`":{`"id`":224223270,`"is_bot`":false,`"first_name`":`"Test`"},`"chat`":{`"id`":224223270,`"first_name`":`"Test`",`"type`":`"private`"},`"date`":1,`"text`":`"$c`"}}"
    try {
        $resp = Invoke-WebRequest -Uri "$BASE/webhook" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
        if ($resp.StatusCode -eq 200) { Write-Host "  OK (200)" -ForegroundColor Green } else { Write-Host "  WARN ($($resp.StatusCode))" -ForegroundColor Yellow }
    } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }
}

# Web endpoints
Write-Host "`n[Web] Admin Page" -ForegroundColor Yellow
try { $code = Invoke-WebRequest -Uri "$BASE/admin" -UseBasicParsing; Write-Host "  OK ($($code.StatusCode))" -ForegroundColor Green } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }

Write-Host "`n[Web] Card Page" -ForegroundColor Yellow
try { $card = Invoke-WebRequest -Uri "$BASE/card/224223270" -UseBasicParsing; Write-Host "  OK ($($card.StatusCode))" -ForegroundColor Green } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }

Write-Host "`n[Railway] Status" -ForegroundColor Yellow
railway status

Write-Host "`n=== All tests completed ===" -ForegroundColor Green
