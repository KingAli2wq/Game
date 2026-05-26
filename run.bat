@echo off
title Grand Strategy AI

echo.
echo  ╔══════════════════════════════════╗
echo  ║     GRAND STRATEGY AI GAME       ║
echo  ║  Hearts of Iron x NationStates   ║
echo  ╚══════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist ".deps_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: pip install failed.
        pause
        exit /b 1
    )
    echo. > .deps_installed
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
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause
