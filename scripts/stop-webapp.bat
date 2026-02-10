@echo off
echo Stopping webapp server...
wsl.exe bash -c "pkill -f 'uvicorn webapp.main:app' 2>/dev/null"
echo Server stopped.
pause
