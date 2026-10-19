@echo off
rem Jalankan CCTV Public Server di Windows:
rem   run.bat
cd /d "%~dp0"

if not exist .venv (
  echo [*] Membuat virtualenv .venv ...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [*] Memasang dependensi ...
pip install -q -r requirements.txt

if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000

echo [*] Server jalan di http://localhost:%PORT%  (docs: /docs)
uvicorn app.main:app --host %HOST% --port %PORT%
