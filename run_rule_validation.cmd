@echo off
setlocal
call "%~dp0_run_python.cmd" validate_rules.py %*
exit /b %errorlevel%
