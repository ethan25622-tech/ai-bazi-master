@echo off
setlocal
call "%~dp0_run_python.cmd" validate_case_library_negative.py %*
exit /b %errorlevel%
