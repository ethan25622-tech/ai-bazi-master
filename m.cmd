@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON%" (
  echo Bundled Python not found: %PYTHON% 1>&2
  exit /b 1
)
"%PYTHON%" mobile_free.py %*
