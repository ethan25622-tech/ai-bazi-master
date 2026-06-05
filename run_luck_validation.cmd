@echo off
setlocal
call "%~dp0_run_python.cmd" validate_luck_cycle.py %*
exit /b %errorlevel%
