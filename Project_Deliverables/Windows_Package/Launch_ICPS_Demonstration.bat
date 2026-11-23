@echo off
setlocal
title ICPS Satellite Avoidance System - Local Demonstration
echo Starting ICPS Demonstration Launcher...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch_ICPS_Demonstration.ps1" %*
endlocal
