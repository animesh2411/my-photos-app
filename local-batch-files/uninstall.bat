@echo off
cd /d "%~dp0.."
:: Self-elevate if not already running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Requesting Administrator privileges to remove firewall...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title PhotoBridge Firewall Uninstaller
echo ======================================================================
echo                 PhotoBridge Firewall Uninstaller
echo ======================================================================
echo.

:: Remove the rule if it exists
echo Checking for existing firewall rule...
powershell -Command "if (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue) { Remove-NetFirewallRule -DisplayName 'PhotoBridge Port 8000'; Write-Host 'Firewall rule [PhotoBridge Port 8000] successfully removed!' } else { Write-Host 'No firewall rule [PhotoBridge Port 8000] was found.' }"

echo.
echo Cleanup completed!
echo.
pause
