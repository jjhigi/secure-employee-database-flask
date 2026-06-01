@echo off
cd /d "%~dp0"
echo ========================================
echo Flask Employee Manager Setup
echo ========================================
echo.

if exist .venv (
    echo Virtual environment already exists. Keeping existing .venv.
) else (
    echo Creating virtual environment...
    py -m venv .venv

    if errorlevel 1 (
        echo.
        echo Setup failed: Python could not create the virtual environment.
        echo Make sure Python is installed and the py launcher works.
        pause
        exit /b 1
    )
)

echo.
echo Installing requirements...
.venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Setup failed: dependencies could not be installed.
    pause
    exit /b 1
)

echo.
echo Creating local .env if needed...
.venv\Scripts\python.exe create_env.py

if errorlevel 1 (
    echo.
    echo Setup failed: .env could not be created.
    pause
    exit /b 1
)

echo.
echo Initializing database tables...
.venv\Scripts\python.exe init_db.py

if errorlevel 1 (
    echo.
    echo Setup failed: database could not be initialized.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo.
echo Next step:
echo Run run.bat to start the app.
echo.
echo If this is your first launch, the app will open the initial admin setup page.
echo Keep the run.bat terminal window open while using the app.
echo.
pause