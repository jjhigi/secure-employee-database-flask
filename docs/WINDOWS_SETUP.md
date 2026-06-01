# Windows Setup Guide

This project is designed to run locally on one Windows computer.

The normal setup flow is:

```text
Download project -> Run setup.bat -> Run run.bat -> Create first admin
```

## Recommended Setup

Double-click:

```bat
setup.bat
```

This script will:

* Create a local virtual environment 
* Install dependencies from `requirements.txt`
* Create `.env` with generated local secrets 
* Initialize the SQLite database tables 

Then double-click:

```bat
run.bat
```

This script starts the Flask app and opens it in your browser.

Keep the terminal window open while using the app. Closing the terminal stops the local Flask server.

## First Admin Setup

On first launch, if the database has no employee records, the app redirects to the initial admin setup page.

Create the first admin account there, then log in normally.

## Starting the App Later

After setup, you usually only need:

```bat
run.bat
```

You do not need to run `setup.bat` every time.

## Windows Smart App Control / Unblock Note

Windows may block `setup.bat` or `run.bat` after downloading the project ZIP from GitHub.

If that happens:

1. Right-click `setup.bat`.
2. Choose **Properties**.
3. On the **General** tab, check **Unblock** if it appears.
4. Click **Apply**.
5. Click **OK**.

Repeat the same steps for:

```text
run.bat
```

Then try running the scripts again.

## Manual Setup

Use these steps only if you do not want to use the Windows batch scripts.

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe create_env.py
.venv\Scripts\python.exe init_db.py
.venv\Scripts\python.exe app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Local Files Created During Setup

Setup creates local files that should stay private:

```text
.env
.venv/
EmployeeDB.db
backups/
```

These are excluded from Git.

## Local Files Not Committed to Git

The following local files and folders should stay private:

```text
.env
.env.*
.venv/
EmployeeDB.db
backups/
__pycache__/
.idea/
PROJECT_NOTES.md
```
