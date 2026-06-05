@echo off
setlocal
call "%~dp0_run_python.cmd" -m bazi_master.cli %*
exit /b %errorlevel%
