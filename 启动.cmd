@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo AI 八字解盘
echo.
echo 1. 输入生日，生成本地报告，然后可继续提问
echo 2. 输入生日，一键复制 GPT/Claude 解盘提示词
echo.
set /p CHOICE=请输入 1 或 2：
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
echo 输入无效，请重新运行。
pause
