@echo off
title Grand Strategy AI

echo.
echo  ╔══════════════════════════════════╗
echo  ║     GRAND STRATEGY AI GAME       ║
echo  ║  Hearts of Iron x NationStates   ║
echo  ╚══════════════════════════════════╝
echo.

:: Prefer venv Python if available
set "PYTHON=python"
set "PIP=pip"
set "DEPS_MARKER=.deps_installed"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    set "PIP=.venv\Scripts\pip.exe"
    set "DEPS_MARKER=.deps_installed_venv"
)

:: Check Python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "%DEPS_MARKER%" (
    echo Installing dependencies...
    %PIP% install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: pip install failed.
        pause
        exit /b 1
    )
    echo. > "%DEPS_MARKER%"
    echo Dependencies installed.
)

:: Kill any existing process on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Starting server at http://localhost:8000
echo Opening browser...
echo Press Ctrl+C to quit.
echo.

:: Open browser after short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Run the server
%PYTHON% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause
