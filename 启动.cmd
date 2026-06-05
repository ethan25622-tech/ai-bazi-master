@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo AI Bazi Master / AI 八字解盘
echo.
echo 1. Local readable report and follow-up questions / 本地报告并继续提问
echo 2. Copy GPT/Claude prompt / 复制 GPT/Claude 提示词
echo.
set /p CHOICE=Please enter 1 or 2 / 请输入 1 或 2: 
if "%CHOICE%"=="1" (
  call "%~dp01.cmd"
  echo.
  pause
  exit /b %errorlevel%
)
if "%CHOICE%"=="2" (
  call "%~dp02.cmd"
  echo.
  pause
  exit /b %errorlevel%
)
echo Invalid input / 输入无效，请重新运行。
pause
