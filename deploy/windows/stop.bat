@echo off
rem AI Resume Server - 停止
taskkill /FI "IMAGENAME eq python.exe" /F >nul 2>&1
echo 已停止所有 python.exe 进程(请注意:这会影响本机其他 Python 程序)
