@echo off
title AgriSuraksha Launcher
cls
echo ====================================================================
echo   AGRISURAKSHA: LIGHTNING ^& FLOOD ALERT REGISTRY FOR FARMERS
echo ====================================================================
echo.

:: 1. Check or start MySQL 8.0 on Port 3307
netstat -ano | findstr ":3307 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [1/3] Launching MySQL 8.0 Daemon on Port 3307...
    start "AgriSuraksha - MySQL 8.0 Database" cmd /k "call \"%~dp0start_mysql.bat\""
    echo Waiting 4 seconds for MySQL database engine to initialize...
    ping 127.0.0.1 -n 5 >nul
) else (
    echo [1/3] MySQL 8.0 Database engine is ALREADY active on Port 3307.
)

:: 2. Check or start Flask Backend on Port 5000
netstat -ano | findstr ":5000 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [2/3] Launching Flask Backend Web Server on Port 5000...
    start "AgriSuraksha - Flask Web App" cmd /k "call \"%~dp0start_app.bat\""
    echo Waiting 3 seconds for Web Server to bind...
    ping 127.0.0.1 -n 4 >nul
) else (
    echo [2/3] Flask Web Server is ALREADY active on Port 5000.
)

:: 3. Open Web Browser
echo.
echo [3/3] Opening Dashboard in your Web Browser...
start http://127.0.0.1:5000

echo.
echo ====================================================================
echo   SUCCESS! All services are active and ready:
echo   - Web Dashboard:  http://127.0.0.1:5000
echo   - MySQL Database: 127.0.0.1:3307 (farmer_alert_db)
echo   - Real-Time Sync: ACTIVE (SSE + BroadcastChannel)
echo ====================================================================
echo.
