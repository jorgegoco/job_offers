@echo off
cd /d %USERPROFILE%
echo ============================================
echo   Job Application Generator - Web App
echo ============================================
echo.
echo Starting server in WSL...
start /min "" wsl.exe bash ~/job_offers/scripts/start-server.sh
echo Waiting for server to boot...
timeout /t 5 /nobreak >nul
echo Opening browser...
start http://localhost:8000
