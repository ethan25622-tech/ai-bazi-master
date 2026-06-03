@echo off
setlocal
set PYTHONIOENCODING=utf-8
set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PYTHON%" (
  echo Bundled Python not found: %PYTHON% 1>&2
  exit /b 1
)
"%PYTHON%" validate_mingli_cases.py %*
