@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 这个入口用于一键生成并复制 GPT/Claude 提示词。
echo.
set /p YEAR=出生年份，例如 1990：
set /p MONTH=出生月份 1-12：
set /p DAY=出生日 1-31：
set /p HOUR=出生小时 0-23：
set /p MINUTE=出生分钟 0-59，直接回车为 0：
if "%MINUTE%"=="" set MINUTE=0
set /p GENDER=性别 男/女：
set /p LONGITUDE=出生地经度，国内不确定直接回车用 120：
if "%LONGITUDE%"=="" set LONGITUDE=120
set /p TARGET_YEAR=想看哪一年流年？不看直接回车：
set /p TARGET_MONTH=想看该年第几个节气流月 1-12？不看直接回车：
set /p QUESTION=想问的问题，直接回车为完整解盘：

set ARGS=--year %YEAR% --month %MONTH% --day %DAY% --hour %HOUR% --minute %MINUTE% --longitude %LONGITUDE% --gender %GENDER%
if not "%TARGET_YEAR%"=="" set ARGS=%ARGS% --target-year %TARGET_YEAR%
if not "%TARGET_MONTH%"=="" set ARGS=%ARGS% --target-month %TARGET_MONTH%
if not "%QUESTION%"=="" set ARGS=%ARGS% --question "%QUESTION%"

call "%~dp0run_llm_prompt_copy.cmd" %ARGS%
pause
