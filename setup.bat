@echo off
:: Self-elevate if not already running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Requesting Administrator privileges to configure firewall...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title PhotoBridge Firewall Setup
echo ======================================================================
echo                 PhotoBridge Firewall Configurator
echo ======================================================================
echo.

:: Add the rule only if it doesn't already exist, scoped to private networks only (not public WiFi)
echo Checking for existing firewall rule...
powershell -Command "if (-not (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private; Write-Host 'Firewall rule [PhotoBridge Port 8000] successfully added for Private networks!' } else { Write-Host 'Firewall rule [PhotoBridge Port 8000] already exists.' }"

echo.
echo Setup completed! You can now access PhotoBridge from other devices on your Wi-Fi network.
echo.
pause
