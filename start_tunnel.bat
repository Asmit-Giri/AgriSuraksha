@echo off
title AgriSuraksha - Live Public Web Tunnel
echo ====================================================================
echo   AGRISURAKSHA: INSTANT PUBLIC INTERNET TUNNEL
echo ====================================================================
echo.
echo Starting secure public HTTPS link for your local app (port 5000)...
echo Share the generated URL with anyone on the internet or smartphone!
echo.
echo (Keep this window open to keep the public URL live. Press Ctrl+C to stop.)
echo ====================================================================
echo.
ssh -R 80:localhost:5000 nokey@localhost.run
pause

