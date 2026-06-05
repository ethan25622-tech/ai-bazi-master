@echo off
setlocal
call "%~dp0_run_python.cmd" validate_phrases.py %*
exit /b %errorlevel%
