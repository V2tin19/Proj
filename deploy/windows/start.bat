@echo off
rem AI Resume Server - 前台启动(调试用;生产用计划任务 install.ps1)
cd /d "%~dp0.."
set "LD_LIBRARY_PATH="
set PYTHONUNBUFFERED=1
if "%PORT%"=="" set PORT=8000
if "%BIND_HOST%"=="" set BIND_HOST=0.0.0.0
echo 启动 AI Resume Server: http://%BIND_HOST%:%PORT%
runtime\python.exe -m uvicorn app.main:app --host %BIND_HOST% --port %PORT%
