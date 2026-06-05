@echo off
cd /d "%~dp0"
echo AI Bazi Master
echo.
echo IMPORTANT:
echo If this is inside a ZIP preview window, close it first.
echo Right-click the ZIP file, choose Extract All, then run START_HERE.bat again.
echo.
echo If Python is missing, install Python 3.11 or newer and check:
echo Add python.exe to PATH
echo.
call "%~dp0ask_bazi.cmd"
echo.
pause
