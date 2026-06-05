@echo off
setlocal
call "%~dp0_run_python.cmd" interactive_report.py
exit /b %errorlevel%
