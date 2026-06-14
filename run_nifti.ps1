# Runner for NIFTI  Bot + API + Cloudflare
Write-Host '🚀 Starting NIFTI...' -ForegroundColor Cyan

\ = Start-Job -Name 'NIFTI_API' -ScriptBlock {
    cd D:\NIFTI
    .\venv\Scripts\Activate.ps1
    \postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME = 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main'
    python main.py
}

\ = Start-Job -Name 'NIFTI_BOT' -ScriptBlock {
    cd D:\NIFTI
    .\venv\Scripts\Activate.ps1
    \8932763531:AAHapArK0V_1fLjX7Ai2pYyCVCP0z3-UUY8 = '7998856873:AAH4x3FvJga8KZE-S49x_MR_T7GtF7BuuH0'
    \ = '224223270'
    \postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME = 'postgresql://postgres:slh_secure_2026@localhost:5432/slh_main'
    python bot.py
}

\ = Start-Process -FilePath 'D:\NIFTI\cloudflared.exe' -ArgumentList 'tunnel --url http://localhost:8000' -NoNewWindow -PassThru

Write-Host '✅ API Job:' \.Id -ForegroundColor Green
Write-Host '✅ Bot Job:' \.Id -ForegroundColor Green
Write-Host '🌍 Cloudflare PID:' \.Id -ForegroundColor Magenta
Write-Host 'הבוט רץ  שלח /market בטלגרם.'
