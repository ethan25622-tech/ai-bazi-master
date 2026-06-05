@echo off
setlocal
call "%~dp0_run_python.cmd" validate_project_status.py %*
exit /b %errorlevel%
