@echo off
echo Setting up Job App Generator...

set LOCAL_DIR=%USERPROFILE%\JobAppGenerator
set LOCAL_BAT=%LOCAL_DIR%\start-webapp.bat
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Job App Generator.lnk

:: Copy launcher to a local Windows folder (avoids security warning)
if not exist "%LOCAL_DIR%" mkdir "%LOCAL_DIR%"
copy /y "%~dp0start-webapp.bat" "%LOCAL_BAT%" >nul
copy /y "%~dp0stop-webapp.bat" "%LOCAL_DIR%\stop-webapp.bat" >nul

:: Create desktop shortcut pointing to the local copy
> "%TEMP%\create_shortcut.vbs" (
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo Set oLink = oWS.CreateShortcut^("%SHORTCUT_PATH%"^)
    echo oLink.TargetPath = "%LOCAL_BAT%"
    echo oLink.WorkingDirectory = "%LOCAL_DIR%"
    echo oLink.Description = "Launch the Job Application Generator webapp"
    echo oLink.IconLocation = "shell32.dll,13"
    echo oLink.Save
)

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo.
echo Done! Files copied to: %LOCAL_DIR%
echo Shortcut created on Desktop: "Job App Generator"
echo.
pause
