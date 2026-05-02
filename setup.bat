@echo off
setlocal
title WisprWin — Setup

echo ============================================================
echo  WisprWin Setup
echo ============================================================
echo.

:: ── Check Python ────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.12+ from python.org
    pause & exit /b 1
)

echo [1/5] Creating virtual environment ...
python -m venv venv
if errorlevel 1 ( echo [ERROR] venv creation failed. & pause & exit /b 1 )

echo.
echo [2/5] Activating venv ...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies ...
pip install -r wisprwin\requirements.txt --quiet
if errorlevel 1 ( echo [ERROR] pip install failed. & pause & exit /b 1 )

echo.
echo [4/4] Generating tray icons ...
python wisprwin\make_icons.py
if errorlevel 1 ( echo [WARN] Icon generation failed - icons will be created on first run. )

echo.
echo ============================================================
echo  Setup complete!
echo ============================================================
echo.
echo  To run WisprWin:
echo    Double-click  start_wispr.bat
echo  OR
echo    Enable "Launch at Windows startup" in Settings so it
echo    starts automatically every time you log in.
echo.
pause
endlocal
