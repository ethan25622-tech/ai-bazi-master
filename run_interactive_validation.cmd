@echo off
setlocal
call "%~dp0_run_python.cmd" validate_interactive_report.py %*
exit /b %errorlevel%
