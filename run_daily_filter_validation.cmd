@echo off
setlocal
call "%~dp0_run_python.cmd" validate_daily_filter.py %*
exit /b %errorlevel%
