@echo off
echo ==========================================================
echo    ENABLING 24x7 AUTO-START ON WINDOWS BOOT
echo ==========================================================
echo.
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /y "%~dp0Run_Silent_Background.vbs" "%STARTUP_DIR%\AI_Job_Sniper_Startup.vbs" >nul

if %errorlevel% equ 0 (
    echo [SUCCESS] AI Job Sniper is now registered in Windows Startup!
    echo Laptop restart hone par bhi yeh silently 24x7 background me start ho jayega.
) else (
    echo [ERROR] Failed to register in Startup.
)
echo.
pause

