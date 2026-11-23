@echo off
setlocal
title ICPS Satellite Avoidance System - Local Demonstration
echo Starting ICPS Demonstration Launcher...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch_ICPS_Demonstration.ps1" %*
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Launcher failed with exit code %ERRORLEVEL%.
    echo ======================================================================
    echo.
    pause
)
endlocal
