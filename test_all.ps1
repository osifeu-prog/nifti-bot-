# NIFTI Auto Test Suite
$TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$BASE = "https://bot-production-c2a5.up.railway.app"

$tests = @(
    @{cmd="/start"; name="Start"},
    @{cmd="/my_card"; name="MyCard"},
    @{cmd="/leaderboard"; name="Leaderboard"},
    @{cmd="/earnings"; name="Earnings"},
    @{cmd="/spin"; name="Spin"},
    @{cmd="/invite"; name="Invite"},
    @{cmd="/status"; name="Status"},
    @{cmd="/docs"; name="Docs"},
    @{cmd="/news"; name="News"},
    @{cmd="/commands"; name="Commands"}
)

$admin_tests = @(
    @{cmd="/admin"; name="Admin"},
    @{cmd="/stats"; name="Stats"},
    @{cmd="/healthcheck"; name="Healthcheck"},
    @{cmd="/check"; name="SystemCheck"}
)

Write-Host "=== NIFTI Auto Test ===" -ForegroundColor Cyan

# 1. API Root
Write-Host "`n[API] Root..." -ForegroundColor Yellow
try { $api = Invoke-RestMethod "$BASE/"; Write-Host "  OK: $($api.status)" -ForegroundColor Green } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }

# 2. Webhook Info
Write-Host "`n[Webhook] Info..." -ForegroundColor Yellow
$web = Invoke-RestMethod "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
Write-Host "  URL: $($web.result.url)" -ForegroundColor Green
Write-Host "  Pending: $($web.result.pending_update_count)" -ForegroundColor $(if($web.result.pending_update_count -eq 0){'Green'}else{'Yellow'})

# 3. Send simulated webhook for each command (as user 224223270)
foreach ($t in $tests) {
    Write-Host "`n[Sim] /$($t.name)..." -ForegroundColor Yellow
    $body = "{`"update_id`":1,`"message`":{`"message_id`":1,`"from`":{`"id`":224223270,`"is_bot`":false,`"first_name`":`"Test`"},`"chat`":{`"id`":224223270,`"first_name`":`"Test`",`"type`":`"private`"},`"date`":1,`"text`":`"$($t.cmd)`"}}"
    try {
        $resp = Invoke-WebRequest -Uri "$BASE/webhook" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
        if ($resp.StatusCode -eq 200) { Write-Host "  OK (200)" -ForegroundColor Green } else { Write-Host "  WARN ($($resp.StatusCode))" -ForegroundColor Yellow }
    } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }
}

# 4. Admin page
Write-Host "`n[Web] Admin Page..." -ForegroundColor Yellow
try { $code = Invoke-WebRequest -Uri "$BASE/admin" -UseBasicParsing; Write-Host "  OK ($($code.StatusCode))" -ForegroundColor Green } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }

# 5. Card page
Write-Host "`n[Web] Card Page..." -ForegroundColor Yellow
try { $card = Invoke-WebRequest -Uri "$BASE/card/224223270" -UseBasicParsing; Write-Host "  OK ($($card.StatusCode))" -ForegroundColor Green } catch { Write-Host "  FAIL: $_" -ForegroundColor Red }

# 6. Railway status
Write-Host "`n[Railway] Status..." -ForegroundColor Yellow
railway status

Write-Host "`n=== All tests completed ===" -ForegroundColor Green
