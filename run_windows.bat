@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher not found. Install Python 3.11 or 3.12 from python.org and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo Could not create a Python 3.12 environment. Check that Python 3.12 is installed.
    pause
    exit /b 1
  )
)
echo Installing/checking dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo.
echo Starting RESCUEGRID at http://127.0.0.1:8000/
echo API docs: http://127.0.0.1:8000/docs
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
goto end
:fail
echo.
echo Dependency installation failed. Read README_WINDOWS.md and check Python version / internet access.
pause
exit /b 1
:end
endlocal
