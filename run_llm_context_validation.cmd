@echo off
setlocal
call "%~dp0_run_python.cmd" validate_llm_context.py
exit /b %errorlevel%
