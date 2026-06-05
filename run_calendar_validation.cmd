@echo off
setlocal
call "%~dp0_run_python.cmd" validate_calendar.py %*
exit /b %errorlevel%
