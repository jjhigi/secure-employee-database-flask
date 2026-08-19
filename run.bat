@echo off
cd /d "%~dp0"
echo ========================================
echo Starting Flask Employee Manager
echo ========================================
echo.

if not exist .venv (
    echo Virtual environment not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

if not exist .env (
    echo .env file not found.
    echo Run setup.bat first.
    pause
    exit /b 1
)

echo Checking database schema...
.venv\Scripts\python.exe init_db.py

if errorlevel 1 (
    echo.
    echo Startup failed: database could not be initialized.
    pause
    exit /b 1
)

echo.
echo Starting Flask app...
echo Keep this terminal window open while using the app.
echo Press Ctrl+C to stop the server.
echo.

start "" http://127.0.0.1:5000

.venv\Scripts\python.exe app.py

echo.
echo Flask Employee Manager has stopped.
pause
