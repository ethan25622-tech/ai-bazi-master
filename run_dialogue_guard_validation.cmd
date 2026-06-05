@echo off
setlocal
call "%~dp0_run_python.cmd" validate_dialogue_guard.py %*
exit /b %errorlevel%
