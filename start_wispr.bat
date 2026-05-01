@echo off
::
:: start_wispr.bat — Silent launcher for WisprWin.
::
:: This file is registered in Windows startup by the app itself
:: when "Launch at startup" is enabled in Settings.
::
:: It activates the venv and starts main.py with no console window.
::

setlocal
:: Resolve the directory this .bat lives in
set "ROOT=%~dp0"

:: Activate the virtual environment
call "%ROOT%venv\Scripts\activate.bat"

:: Launch WisprWin — pythonw.exe hides the console window
start "" pythonw "%ROOT%wisprwin\main.py"
endlocal
