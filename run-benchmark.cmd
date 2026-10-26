@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo ERROR: Python environment missing. Create it with: py -m venv .venv
  exit /b 2
)
if /i "%~1"=="quick" (
  "%PYTHON%" tools\benchmark\run_suite.py --limit 10 --modes both
) else (
  "%PYTHON%" tools\benchmark\run_suite.py --modes both
)
exit /b %errorlevel%
