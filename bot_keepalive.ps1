while ($true) {
    cd D:\NIFTI
    .\venv\Scripts\Activate.ps1
    $env:BOT_TOKEN = "NEW_TOKEN"
    $env:ADMIN_USER_ID = "224223270"
    $env:DATABASE_URL = "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"
    python bot.py
    Write-Host "Bot stopped. Restarting in 5 seconds..." -ForegroundColor Yellow
    Start-Sleep 5
}
