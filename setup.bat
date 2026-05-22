@echo off
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
echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Installing requirements...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Setup failed: dependencies could not be installed.
    pause
    exit /b 1
)

echo.
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env

    if errorlevel 1 (
        echo.
        echo Setup failed: .env could not be created.
        pause
        exit /b 1
    )
) else (
    echo .env already exists. Keeping existing local configuration.
)

echo.
echo Initializing database tables...
python init_db.py

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