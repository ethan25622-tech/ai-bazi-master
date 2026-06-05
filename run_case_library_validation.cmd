@echo off
setlocal
call "%~dp0_run_python.cmd" validate_case_library.py %*
exit /b %errorlevel%
