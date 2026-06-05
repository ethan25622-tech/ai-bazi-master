@echo off
setlocal
call "%~dp0_run_python.cmd" validate_luck_guard.py %*
exit /b %errorlevel%
