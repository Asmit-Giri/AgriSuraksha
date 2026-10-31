@echo off
setlocal enabledelayedexpansion
echo ========================================================
echo  Lightning ^& Flood Alert Registry - MySQL 8.0 Startup
echo ========================================================

:: 1. Check if MySQL is already listening on Port 3307
netstat -ano | findstr ":3307 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] MySQL Server is ALREADY running and active on Port 3307.
    echo [INFO] No duplicate instance needed.
    echo.
    exit /b 0
)

:: 2. Locate data directory (where seeded farmers, alerts & telemetry exist)
set DATADIR=C:\Users\asmit\.gemini\antigravity\scratch\farmer-alert-registry\mysql_data

if not exist "!DATADIR!" (
    set DATADIR=%~dp0mysql_data
    echo [INFO] Scratch datadir not found. Using local: !DATADIR!
    if not exist "!DATADIR!" (
        echo [INIT] Initializing fresh local MySQL data directory...
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --initialize-insecure --datadir="!DATADIR!" --console
    )
) else (
    echo [INFO] Using database directory: !DATADIR!
)

echo.
echo [START] Launching mysqld on port 3307...
echo [INFO]  Keep this window open to maintain the database connection.
echo.
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --datadir="!DATADIR!" --port=3307 --mysqlx=0 --console
pause
