@echo off
setlocal
call "%~dp0_run_python.cmd" -m bazi_master.cli --llm-prompt --copy-only %*
exit /b %errorlevel%
