@echo off
setlocal
call "%~dp0_run_python.cmd" mobile_free.py %*
exit /b %errorlevel%
