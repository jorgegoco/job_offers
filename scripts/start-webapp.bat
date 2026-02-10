@echo off
echo ============================================
echo   Job Application Generator - Web App
echo ============================================
echo.
echo Starting server in WSL...
start /min "" wsl.exe bash -c "cd ~/job_offers && uvicorn webapp.main:app --host 0.0.0.0 --port 8000"
echo Waiting for server to boot...
timeout /t 3 /nobreak >nul
echo Opening browser...
start http://localhost:8000
echo.
echo ============================================
echo   Server is running at http://localhost:8000
echo.
echo   To stop: run stop-webapp.bat
echo   Or close the minimized WSL window
echo ============================================
echo.
pause
