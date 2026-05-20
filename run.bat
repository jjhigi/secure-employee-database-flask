@echo off
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

call .venv\Scripts\activate

echo Opening app in browser...
start http://127.0.0.1:5000

echo.
echo Starting Flask app...
echo Press Ctrl+C to stop the server.
echo.
python app.py

pause