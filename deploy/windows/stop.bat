@echo off
rem AI Resume Server - 停止
powershell -NoProfile -Command "Stop-ScheduledTask -TaskName 'AIResumeServer' -ErrorAction SilentlyContinue; Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*ai-resume-server*' } | Stop-Process -Force" >nul 2>&1
echo 已停止所有 python.exe 进程(请注意:这会影响本机其他 Python 程序)
