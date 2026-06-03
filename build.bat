@echo off
::
:: build.bat — Build WisprWin into a single .exe with PyInstaller.
::
:: Prerequisites:
::   1. Run setup.bat first to create the venv
::   2. pip install pyinstaller (inside the venv)
::
:: Output: dist/WisprWin.exe
::

setlocal
title WisprWin — Build

echo ============================================================
echo  WisprWin Build
echo ============================================================
echo.

:: Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause & exit /b 1
)

:: Ensure PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [1/3] Installing PyInstaller ...
    pip install pyinstaller --quiet
) else (
    echo [1/3] PyInstaller already installed.
)

:: Generate icons (including .ico)
echo.
echo [2/3] Generating icons ...
python apply_logo.py

:: Build
echo.
echo [3/3] Building WisprWin.exe ...
pyinstaller ^
    --onefile ^
    --windowed ^
    --icon=wisprwin\assets\icon.ico ^
    --name=WisprWin ^
    --add-data "wisprwin\assets;assets" ^
    --collect-data faster_whisper ^
    wisprwin\main.py

echo.
if exist "dist\WisprWin.exe" (
    echo ============================================================
    echo  Build successful!
    echo  Output: dist\WisprWin.exe
    echo ============================================================
) else (
    echo [ERROR] Build failed. Check output above for errors.
)

echo.
pause
endlocal
