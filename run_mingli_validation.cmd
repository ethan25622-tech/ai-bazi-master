@echo off
setlocal
call "%~dp0_run_python.cmd" validate_mingli_cases.py %*
exit /b %errorlevel%
