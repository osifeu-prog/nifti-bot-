# NIFTI Final Launcher v1.0
$ErrorActionPreference = "Stop"
$root = (Get-Location).Path
Set-Location $root

# Kill old processes
taskkill /F /IM python.exe 2>$null
taskkill /F /IM cloudflared.exe 2>$null

# Activate venv
. "$root\venv\Scripts\Activate.ps1"

# Environment variables
$env:BOT_TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$env:ADMIN_USER_ID = "224223270"
$env:DATABASE_URL = "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " NIFTI Production Launcher v2.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check PostgreSQL
Write-Host "`n[1/4] Checking PostgreSQL..." -ForegroundColor Yellow
try {
    python -c "import asyncio,asyncpg; asyncio.run(asyncpg.connect('$env:DATABASE_URL')); print('DB OK')"
} catch {
    Write-Error "PostgreSQL not reachable. Please start it and re-run."
    exit 1
}

# Cloudflare Tunnel
Write-Host "`n[2/4] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "$root\cloudflared.exe" -ArgumentList "tunnel --url http://localhost:8000"
Start-Sleep 4

# TON Scanner (background)
Write-Host "`n[3/4] Starting TON Scanner..." -ForegroundColor Yellow
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd $root; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$env:DATABASE_URL'; python ton_scanner.py"

# API server (background)
Write-Host "`n[4/4] Starting API server..." -ForegroundColor Yellow
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd $root; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$env:DATABASE_URL'; python main.py"

# Wait for API health
Write-Host "   Waiting for API..." -ForegroundColor Gray
Start-Sleep 5
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health/db" -UseBasicParsing -TimeoutSec 3
    Write-Host "   API is healthy: $($health.Content)" -ForegroundColor Green
} catch {
    Write-Warning "API health check failed, but continuing..."
}

# Bot (foreground, auto-restart)
Write-Host "`n[Bot] Starting NIFTI Bot (auto-restart on crash)..." -ForegroundColor Cyan
while ($true) {
    python bot.py 2>&1 | Tee-Object -FilePath "$root\bot_log.txt" -Append
    Write-Host "Bot stopped. Restarting in 5 seconds..." -ForegroundColor Yellow
    Start-Sleep 5
}
