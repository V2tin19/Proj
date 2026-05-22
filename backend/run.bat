@echo off
cd /d "%~dp0"
set PORT=8000
venv\Scripts\python.exe -m uvicorn app.main:app --port %PORT% --reload
