@echo off
setlocal
set PYTHONIOENCODING=utf-8

call :run run_rule_validation.cmd
if errorlevel 1 exit /b 1

call :run run_calendar_validation.cmd
if errorlevel 1 exit /b 1

call :run run_luck_validation.cmd
if errorlevel 1 exit /b 1

call :run run_month_validation.cmd
if errorlevel 1 exit /b 1

call :run run_luck_guard_validation.cmd
if errorlevel 1 exit /b 1

call :run run_daily_filter_validation.cmd
if errorlevel 1 exit /b 1

call :run run_phrase_validation.cmd
if errorlevel 1 exit /b 1

call :run run_dialogue_guard_validation.cmd
if errorlevel 1 exit /b 1

call :run run_report_validation.cmd
if errorlevel 1 exit /b 1

call :run run_interactive_validation.cmd
if errorlevel 1 exit /b 1

call :run run_llm_context_validation.cmd
if errorlevel 1 exit /b 1

call :run run_case_library_validation.cmd
if errorlevel 1 exit /b 1

call :run run_case_library_negative_validation.cmd
if errorlevel 1 exit /b 1

call :run run_mingli_validation.cmd
if errorlevel 1 exit /b 1

call :run run_project_status_validation.cmd
if errorlevel 1 exit /b 1

echo.
echo ALL VALIDATIONS PASSED
exit /b 0

:run
echo.
echo ==== %~1 ====
call "%~1"
exit /b %errorlevel%
