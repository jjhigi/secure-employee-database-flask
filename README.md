# Flask Employee Manager

A local-first Flask web application for managing employee records and pay raise data.

This project demonstrates practical database security concepts in a small local employee/pay-raise database, including authentication, role-based authorization, password hashing, encrypted fields, CSRF protection, validation, backups, safe restore, audit logging, and authenticated socket messaging.

The goal is a secure, usable local database that runs on one admin computer with minimal setup. It is not intended to be an enterprise HR system, public web app, SaaS app, or intranet app.

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Templates:** Jinja2 server-rendered HTML
- **Styling:** CSS
- **Authentication:** Flask sessions, Werkzeug password hashing
- **Authorization:** Role-based security levels
- **Encryption:** AES through PyCryptodome
- **Message Authentication:** HMAC with SHA3-512
- **Form Protection:** Flask-WTF CSRF protection
- **Configuration:** Local `.env` file loaded through `config.py`

## Main Features

### Employee Management

- Create the first admin account when the database is empty
- Add, edit, list, search, deactivate, and reactivate employees
- Reset employee passwords as an admin
- Change your own password while logged in
- Store employee passwords as hashes, never plaintext
- Encrypt selected employee fields at rest

### Pay Raise Management

- Add pay raise records directly through Flask
- View all pay raises as a Level 1 admin or Level 2 manager
- View active pay raises for the currently logged-in user
- Filter pay raises by employee ID, date range, and minimum amount
- Store pay raise amounts with AES encryption
- Void pay raise records instead of permanently deleting them
- Submit encrypted socket-based pay raise void requests
- Submit encrypted and HMAC-authenticated socket-based pay raise creation requests

### Database Utilities

- Safely initialize database tables without deleting data
- Seed demo data for local testing
- Reset and rebuild the demo database intentionally
- Create timestamped local database backups
- Restore from backup with a safety backup created first
- Record selected sensitive actions in an audit log

## Security Highlights

- Passwords are stored with Werkzeug password hashing.
- Passwords are never displayed back to users.
- Role-based access control protects employee, pay raise, and audit routes.
- Sessions are revalidated against the current database user, active status, and stored password hash.
- Inactive accounts cannot log in.
- First-admin setup is only available when the database is empty.
- Selected employee and pay raise fields are encrypted at rest using AES with a random IV per encrypted value.
- CSRF protection is enabled through Flask-WTF.
- Session cookies use `HttpOnly` and `SameSite=Lax`.
- Sensitive account actions are written to the `AuditLog` table.
- Audit log filters use parameterized SQL.
- Pay raise records are voided instead of permanently deleted.
- Local secrets, databases, backups, virtual environments, IDE files, and project notes are excluded from Git.
- HMAC validation helps detect tampered add-pay-raise socket messages.

More detailed security notes will be documented in `SECURITY.md`.

## Security Levels

| Level | Role | Main Permissions |
|-------|------|------------------|
| 1 | Admin | Manage employees, reset passwords, deactivate/reactivate accounts, view audit logs, list all pay raises, and void pay raises |
| 2 | Manager | List employees, list all pay raises, and void pay raises |
| 3 | Employee | View own pay raises, add own pay raises, and change own password |

## Getting Started

### Recommended Windows Setup

From GitHub, clone the project:

```bash
git clone https://github.com/jjhigi/secure-employee-database-flask.git
cd secure-employee-database-flask
```

Or download the ZIP from GitHub, extract it, and open the extracted project folder.

Run:

```bash
setup.bat
```

This script will:

- Create a local virtual environment if needed
- Install dependencies from `requirements.txt`
- Create `.env` with generated local secrets if needed
- Initialize the SQLite database tables without deleting existing data

Then start the app:

```bash
run.bat
```

This script will activate the virtual environment, open the app in your browser, and start the Flask development server.

Keep the terminal window open while using the app. Closing the terminal stops the local Flask server.

Open manually if needed:

```text
http://127.0.0.1:5000
```

On first launch, if the database has no employee records, the app redirects to the initial admin setup page. Create the first admin account there, then log in normally.

### Starting the App Later

After setup, you usually only need:

```bash
run.bat
```

You do not need to run `setup.bat` every time.

## Manual Setup

Use these steps only if you do not want to use the Windows batch scripts.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python create_env.py
python init_db.py
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Optional demo data:

```bash
python seed_demo.py
```

If demo data is seeded, the sample users use:

```text
Password: test123
```

Example demo login:

```text
Username: PDiana
Password: test123
```

## Database Commands

```bash
# Safely create database tables without deleting existing data
python init_db.py

# Add demo data to an empty database
python seed_demo.py

# Create a timestamped backup
python backup_db.py

# Restore from a backup in backups/
python restore_db.py EmployeeDB_YYYY-MM-DD_HH-MM-SS.db

# Intentionally reset and rebuild the demo database
python reset_demo_db.py

# Backward-compatible reset command
python setup.py
```

> **Warning:** `reset_demo_db.py` and `setup.py` delete existing `Employee`, `EmpPayRaise`, and `AuditLog` records before recreating demo data. Use `init_db.py` for safe setup.

## Socket Server Features

Some pay raise features use separate local TCP socket servers.

Start the Flask app:

```bash
python app.py
```

Start the encrypted pay raise void server in another terminal:

```bash
python ProcessPayRaiseDeletionsServer.py
```

Start the authenticated add-pay-raise server in another terminal:

```bash
python AddAPayRaiseServer.py
```

For full socket functionality, run all three processes at the same time.

## Architecture

```text
Browser  -->  Flask App  -->  SQLite Database
                  |
                  | encrypted socket message
                  v
          TCP Server for Pay Raise Voiding

Browser  -->  Flask App  -->  encrypted + HMAC socket message
                  |
                  v
          TCP Server for Pay Raise Creation  -->  SQLite Database
```

## Application Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET / POST | `/setup-admin` | No | Create the first admin account when the Employee table is empty |
| GET / POST | `/login` | No | Sign in with employee credentials |
| GET | `/logout` | Yes | Log out current user |
| GET | `/` | Yes | Home page |
| GET / POST | `/changepassword` | Yes | Change the current user's password |
| GET | `/addemployee` | Level 1 | Show add employee form |
| POST | `/addrec` | Level 1 | Create a new employee |
| GET | `/listemployees` | Level 1 or 2 | List and search employee records |
| GET / POST | `/editemployee/<user_id>` | Level 1 | Edit an employee record |
| GET / POST | `/resetpassword/<user_id>` | Level 1 | Reset an employee password |
| POST | `/deactivateemployee/<user_id>` | Level 1 | Mark an employee account inactive |
| POST | `/reactivateemployee/<user_id>` | Level 1 | Reactivate an employee account |
| GET | `/auditlog` | Level 1 | View and filter audit log entries |
| GET | `/listpayraises` | Level 1 or 2 | List and filter all pay raise records |
| GET | `/mypayraises` | Yes | Show current user's active pay raises |
| GET / POST | `/addpayraise` | Yes | Add pay raise directly through Flask |
| GET / POST | `/submitdeletepayraise` | Level 1 or 2 | Send encrypted void request to TCP server |
| GET / POST | `/sendaddpayraisehmac` | Yes | Send encrypted and authenticated add-pay-raise message |

## Project Structure

```text
flask-employee-manager/
├── app.py
├── config.py
├── .env.example
├── init_db.py
├── seed_demo.py
├── reset_demo_db.py
├── backup_db.py
├── restore_db.py
├── setup.py
├── setup.bat
├── run.bat
├── Encryption.py
├── ProcessPayRaiseDeletionsServer.py
├── AddAPayRaiseServer.py
├── audit.py
├── auth_helpers.py
├── crypto_helpers.py
├── db.py
├── validation_constants.py
├── routes/
│   ├── auth_routes.py
│   ├── employee_routes.py
│   └── payraise_routes.py
├── static/
│   └── styles.css
└── templates/
    └── ...
```

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

## Limitations

- Designed for local use on one admin computer
- Uses the Flask development server
- Not packaged as a native desktop app
- Terminal window must stay open while the app is running
- Long-term encryption key rotation is not implemented
- Backup files must be protected by the local computer/user
- Not intended for real employee data without further security review

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration only. Demo accounts use the password `test123`, stored as a hash.

## Author

Jeffrey Higi