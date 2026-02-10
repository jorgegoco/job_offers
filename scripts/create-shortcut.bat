@echo off
echo Creating desktop shortcut...

set SCRIPT_DIR=%~dp0
set BAT_PATH=%SCRIPT_DIR%start-webapp.bat
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Job App Generator.lnk

> "%TEMP%\create_shortcut.vbs" (
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo Set oLink = oWS.CreateShortcut^("%SHORTCUT_PATH%"^)
    echo oLink.TargetPath = "%BAT_PATH%"
    echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
    echo oLink.Description = "Launch the Job Application Generator webapp"
    echo oLink.IconLocation = "shell32.dll,13"
    echo oLink.Save
)

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo.
echo Shortcut created on Desktop: "Job App Generator"
echo.
pause
