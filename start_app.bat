@echo off
echo ========================================================
echo  Starting AgriSuraksha Flask Web Application...
echo ========================================================

:: 1. Check if Flask is already running on Port 5000
netstat -ano | findstr ":5000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Flask Web App is ALREADY running and active on Port 5000.
    echo [INFO] Open your browser at: http://127.0.0.1:5000
    echo.
    exit /b 0
)

cd /d "%~dp0"
"C:\Users\asmit\AppData\Local\Programs\Python\Python314\python.exe" app.py
pause
