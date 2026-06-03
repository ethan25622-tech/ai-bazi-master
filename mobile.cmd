@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

if "%~1"=="" (
  set "USAGE_EXIT=2"
  goto usage
)
set "MODE=%~1"
shift /1

set "ARGS="
:collect_args
if "%~1"=="" goto dispatch
set ARGS=%ARGS% "%~1"
shift /1
goto collect_args

:dispatch
if /I "%MODE%"=="prompt" goto prompt
if /I "%MODE%"=="prompt-copy" goto prompt_copy
if /I "%MODE%"=="report" goto report
if /I "%MODE%"=="reply" goto reply
if /I "%MODE%"=="json" goto json
if /I "%MODE%"=="status" goto status
if /I "%MODE%"=="validate" goto validate
if /I "%MODE%"=="help" (
  set "USAGE_EXIT=0"
  goto usage
)
set "USAGE_EXIT=2"
goto usage

:prompt
call "%~dp0run_llm_prompt.cmd" %ARGS%
exit /b %errorlevel%

:prompt_copy
call "%~dp0run_llm_prompt.cmd" --copy %ARGS%
exit /b %errorlevel%

:report
call "%~dp0run_report.cmd" %ARGS%
exit /b %errorlevel%

:reply
call "%~dp0run_master.cmd" --reply-only %ARGS%
exit /b %errorlevel%

:json
call "%~dp0run_master.cmd" %ARGS%
exit /b %errorlevel%

:status
call "%~dp0run_project_status_validation.cmd" %ARGS%
exit /b %errorlevel%

:validate
call "%~dp0run_all_validation.cmd" %ARGS%
exit /b %errorlevel%

:usage
echo Mobile/OpenClaw entrypoint
echo.
echo Usage:
echo   mobile.cmd prompt [birth args]       Print GPT/Claude prompt to phone
echo   mobile.cmd prompt-copy [birth args]  Print prompt and copy it on PC
echo   mobile.cmd report [birth args]       Print readable local report
echo   mobile.cmd reply [birth args] --question "..."
echo   mobile.cmd json [birth args]         Print raw stable JSON
echo   mobile.cmd status                    Run project acceptance check
echo   mobile.cmd validate                  Run full validation suite
echo.
echo Example:
echo   mobile.cmd prompt --year 1990 --month 1 --day 1 --hour 12 --minute 0 --longitude 120 --gender ? --target-year 2028 --question "?????"
if not defined USAGE_EXIT set "USAGE_EXIT=2"
exit /b %USAGE_EXIT%
