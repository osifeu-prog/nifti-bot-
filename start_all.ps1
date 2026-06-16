# NIFTI  Start All Services
cd D:\NIFTI
.\venv\Scripts\Activate.ps1

taskkill /F /IM python.exe 2>$null
taskkill /F /IM cloudflared.exe 2>$null

$env:BOT_TOKEN = "7998856873:AAHq0k3NEstfjbES6zgk6nOCeSycR4iqrO0"
$env:ADMIN_USER_ID = "224223270"
$env:DATABASE_URL = "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main"

# Cloudflare Tunnel
Start-Process -NoNewWindow -FilePath ".\cloudflared.exe" -ArgumentList "tunnel --url http://localhost:8000"

# TON Scanner
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd D:\NIFTI; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$env:DATABASE_URL'; python ton_scanner.py"

# API Server (FastAPI)
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "cd D:\NIFTI; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$env:DATABASE_URL'; python main.py"

# Bot (foreground)
python bot.py 2>&1 | Tee-Object -FilePath bot_log.txt
