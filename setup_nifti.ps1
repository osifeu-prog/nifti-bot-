# NIFTI Setup Script
Write-Host "Configuring NIFTI Terminal OS..." -ForegroundColor Magenta

# 1. Setup Profile
$profilePath = $PROFILE
if (!(Test-Path $profilePath)) { New-Item -ItemType File -Path $profilePath -Force }

# 2. Add Dashboard Alias
$dashboardScript = @"
function Clear-Screen {
    [Console]::Clear()
    Write-Host "=== NIFTI DASHBOARD ===" -ForegroundColor Cyan
    `$tasks = Get-Content "D:\NIFTI\open_tasks.txt"
    # Logic to show ETA...
    Write-Host "System Ready. Current Project: NIFTI" -ForegroundColor Green
}
Set-Alias cls Clear-Screen
"@
Add-Content -Path $profilePath -Value $dashboardScript

Write-Host "Done! Restart your PowerShell." -ForegroundColor Green
