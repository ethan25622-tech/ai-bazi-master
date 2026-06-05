@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

set "PYTHON_CMD="
if exist "%~dp0runtime\python\python.exe" set PYTHON_CMD="%~dp0runtime\python\python.exe"

if defined PYTHON_CMD goto run_python

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
  )
)

if not defined PYTHON_CMD (
  set "CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if exist "%CODEX_PYTHON%" set PYTHON_CMD="%CODEX_PYTHON%"
)

if not defined PYTHON_CMD goto missing_python

:run_python
%PYTHON_CMD% %*
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" goto python_error
exit /b 0

:missing_python
echo.
echo Python runtime was not found.
echo.
echo The downloaded package may be incomplete.
echo Please download the ZIP again, extract the whole folder, and run the launcher again.
echo.
echo If you are using the source-only package, install Python 3.11 or newer from:
echo https://www.python.org/downloads/windows/
echo.
echo During installation, please check: Add python.exe to PATH
echo.
pause
exit /b 1

:python_error
echo.
echo Program exited with error code %ERR%.
echo.
echo If you are running from inside a ZIP preview window:
echo 1. Close this window.
echo 2. Right-click the ZIP file.
echo 3. Choose Extract All.
echo 4. Open the extracted folder.
echo 5. Run the launcher .bat file again.
echo.
pause
exit /b %ERR%
