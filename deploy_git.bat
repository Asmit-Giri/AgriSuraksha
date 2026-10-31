@echo off
title AgriSuraksha - Push to GitHub
echo ====================================================================
echo   AGRISURAKSHA: PUSH UPDATES TO GITHUB REPOSITORY
echo   Repo: https://github.com/Asmit-Giri/AgriSuraksha.git
echo ====================================================================
echo.
cd /d "%~dp0"
git add .
git commit -m "Configure production cloud deployment (Render, Railway, Docker, WSGI)"
echo.
echo Pushing to GitHub...
git push origin main
echo.
echo ====================================================================
echo   SUCCESS! Pushed to https://github.com/Asmit-Giri/AgriSuraksha
echo ====================================================================
pause
