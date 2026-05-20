# Flask Employee Manager

A local-first Flask web application for managing employee records and pay raise data.

This project is a database security exercise built around a small local employee/pay-raise database. It demonstrates authentication, authorization, password hashing, encrypted fields, CSRF protection, validation, local backups, safe restore, audit logging, protected form submissions, and authenticated socket messaging.

The goal is a secure, usable local employee database that runs on one admin computer with minimal setup. It is not intended to be an enterprise HR system, public web app, SaaS app, or intranet app.

## Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite
- **Templates:** Server-rendered HTML + Jinja2
- **Styling:** CSS
- **Authentication:** Flask sessions + Werkzeug password hashing
- **Authorization:** Role-based security levels
- **Encryption:** AES through PyCryptodome
- **Message Authentication:** HMAC with SHA3-512
- **Networking:** Python TCP sockets
- **Form Protection:** Flask-WTF CSRF protection
- **Configuration:** Local `.env` file loaded through `config.py`

## Security Features

- Passwords are stored with Werkzeug password hashing.
- Plaintext employee passwords are never displayed.
- Logged-in users can change their own passwords.
- Password changes require the current password.
- Admin users can reset employee passwords without viewing existing passwords.
- Inactive employee accounts cannot log in.
- Admin users can deactivate employee accounts.
- Admin users can reactivate inactive employee accounts.
- Admin users cannot deactivate their own account.
- First admin setup is only available when the `Employee` table is empty.
- The `/` route redirects to `/setup-admin` when no employee records exist.
- After the first employee account exists, `/setup-admin` is blocked.
- Role-based access control restricts routes by employee security level.
- Unauthorized protected pages use the app's existing 404 behavior.
- Sessions are checked against the current database user.
- Sessions are checked against the current stored password hash.
- Stale sessions are cleared when the database user no longer matches the session.
- Stale sessions are cleared when the stored password hash no longer matches the session.
- Selected employee fields are encrypted at rest.
- Selected pay raise fields are encrypted at rest.
- AES encryption uses a random IV for each encrypted value.
- Shared encryption helpers are centralized in `crypto_helpers.py`.
- Form submissions are protected with Flask-WTF CSRF protection.
- Session cookies use `HttpOnly`.
- Session cookies use `SameSite=Lax`.
- Flask debug mode is controlled by local environment configuration.
- Flask secret key, AES secret, and HMAC secret are loaded from local `.env` configuration.
- `.env` is excluded from Git.
- Local SQLite database files are excluded from Git.
- Local backup files are excluded from Git.
- Local database backups can be created with `backup_db.py`.
- Database restore creates a safety backup before replacing the current database.
- Database initialization can create missing tables without deleting existing data.
- Demo reset scripts are separated from safe initialization scripts.
- Sensitive account actions are recorded in the `AuditLog` table.
- Audit log records include action, user ID, details, and timestamp.
- Admin users can view audit log entries.
- Admin users can filter audit log entries by action, user ID, date range, and details text.
- Audit log queries use parameterized SQL.
- Employee list search is performed without exposing password hashes.
- Pay raise list filters use validated query inputs.
- Pay raise amount validation rejects blank, non-numeric, zero, negative, and oversized values.
- Pay raise date validation rejects blank, invalid, too-old, and future dates.
- Encrypted TCP socket messages are used for pay raise deletion requests.
- HMAC-authenticated encrypted TCP socket messages are used for pay raise creation requests.
- HMAC validation helps detect tampered add-pay-raise socket messages.
- Database access is centralized through `get_db()`.
- Shared authorization checks are centralized in `auth_helpers.py`.
- Sensitive account actions use the shared `log_audit()` helper.

## Main Features

### Employee Management

- Create the first administrator account when the database is empty
- Add employee records
- Edit employee records
- Search employees by name, user ID, security level, or active/inactive status
- Deactivate employee accounts
- Reactivate employee accounts
- Reset employee passwords as an admin
- Change your own password while logged in
- View employee records without displaying passwords

### Pay Raise Management

- Add pay raise records directly through Flask
- View all pay raise records by permission level
- Filter pay raise records by employee ID, date range, and minimum amount
- View pay raises for the currently logged-in user
- Store pay raise amounts with AES encryption
- Submit encrypted socket-based pay raise deletion requests
- Submit encrypted and HMAC-authenticated socket-based pay raise creation requests

### Database Utilities

- Initialize database tables without deleting existing data
- Seed demo data for local testing
- Reset and rebuild the demo database intentionally
- Create timestamped local database backups
- Restore a database backup from the `backups/` folder
- Create a safety backup before restoring over the current database
- Record and filter selected sensitive actions in the `AuditLog` table
- Start setup and app launch with Windows batch scripts

## Current Limitations

- This app is designed for local use on one admin computer.
- It uses the Flask development server.
- It is not packaged as a native desktop app.
- Long-term encryption key rotation is not implemented.
- Backup files must still be protected by the local computer/user.
- It should not be used with real employee data without further review.

## Getting Started

### Recommended Local Setup on Windows

From GitHub, download or clone the project folder first:

```bash
git clone https://github.com/jjhigi/secure-employee-database-flask.git
cd secure-employee-database-flask
```

Or download the ZIP from GitHub, extract it, and open the extracted project folder.

Then run:

```bash
setup.bat
```

This script will:

- Create a local virtual environment if one does not already exist
- Install Python dependencies from `requirements.txt`
- Create `.env` from `.env.example` if `.env` does not already exist
- Initialize the SQLite database tables without deleting existing data

After setup finishes, start the app:

```bash
run.bat
```

This script will:

- Activate the local virtual environment
- Open the app in the browser
- Start the Flask development server

Open manually if needed:

```text
http://127.0.0.1:5000
```

On first launch, if the database has no employee records, the app redirects to the initial admin setup page. Create the first admin account there, then log in normally.

### Starting the App Later

After the first setup, you usually only need to run:

```bash
run.bat
```

You do not need to run `setup.bat` every time.

### Manual Setup

Use these steps only if you do not want to use the Windows batch scripts.

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
copy .env.example .env
```

Create the SQLite database tables without deleting existing data:

```bash
python init_db.py
```

Optionally add demo employee and pay raise data:

```bash
python seed_demo.py
```

Start the Flask application:

```bash
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

### Demo Login

If you seeded demo data, you can log in with:

```text
Username: PDiana
Password: test123
```

Other seeded demo users also use:

```text
Password: test123
```

## Initial Admin Setup

If the database has no employee records, opening the app at:

```text
http://127.0.0.1:5000
```

automatically redirects to:

```text
http://127.0.0.1:5000/setup-admin
```

After the first employee account exists, this setup page is blocked.

## Database Commands

```bash
# Safely create database tables without deleting existing data
python init_db.py

# Add demo data to an empty database
python seed_demo.py

# Create a timestamped backup of the local SQLite database
python backup_db.py

# Restore the local SQLite database from a backup in backups/
python restore_db.py EmployeeDB_YYYY-MM-DD_HH-MM-SS.db

# Intentionally reset and rebuild the demo database
python reset_demo_db.py

# Backward-compatible reset command
python setup.py
```

> **Warning:** `reset_demo_db.py` and `setup.py` delete existing `Employee`, `EmpPayRaise`, and `AuditLog` records before recreating the demo database. Use `init_db.py` for safer setup.

## Socket Server Features

Some pay raise features use separate local TCP socket servers.

Start the main Flask app:

```bash
python app.py
```

Start the encrypted pay raise deletion server in a separate terminal:

```bash
python ProcessPayRaiseDeletionsServer.py
```

Start the authenticated add-pay-raise server in another separate terminal:

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
          TCP Server for Pay Raise Deletion

Browser  -->  Flask App  -->  encrypted + HMAC socket message
                  |
                  v
          TCP Server for Pay Raise Creation  -->  SQLite Database
```

- Flask handles app setup, routing, login, sessions, validation, and page rendering.
- SQLite stores employee, pay raise, and audit log records locally.
- Jinja templates render server-side pages.
- Flask Blueprints separate authentication, employee/admin, and pay raise routes.
- Passwords are stored as one-way hashes.
- AES encryption protects selected stored values.
- Role-based security levels control protected pages.
- Audit logging records selected sensitive account actions.
- Socket servers demonstrate encrypted local client/server communication.
- HMAC validation helps verify that add-pay-raise socket messages were not tampered with.

## Application Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET / POST | `/setup-admin` | No | Create the first admin account when the Employee table is empty |
| GET / POST | `/login` | No | Sign in with employee credentials |
| GET | `/logout` | Yes | Log out current user |
| GET | `/` | Yes | Home page with navigation links |
| GET / POST | `/changepassword` | Yes | Change the current logged-in user's password |
| GET | `/addemployee` | Level 1 | Show add employee form |
| POST | `/addrec` | Level 1 | Create a new employee with a hashed password |
| GET | `/listemployees` | Level 1 or 2 | List and search employee records |
| GET / POST | `/editemployee/<user_id>` | Level 1 | Edit an employee record |
| GET / POST | `/resetpassword/<user_id>` | Level 1 | Reset an employee password |
| POST | `/deactivateemployee/<user_id>` | Level 1 | Mark an employee account as inactive |
| POST | `/reactivateemployee/<user_id>` | Level 1 | Reactivate an inactive employee account |
| GET | `/auditlog` | Level 1 | View and filter sensitive account action history |
| GET | `/listpayraises` | Level 2 | List and filter all pay raise records |
| GET | `/mypayraises` | Yes | Show current user's pay raises |
| GET / POST | `/addpayraise` | Yes | Add pay raise directly through Flask |
| GET / POST | `/submitdeletepayraise` | Level 1 or 2 | Send encrypted delete request to TCP server |
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
│   ├── __init__.py
│   ├── auth_routes.py
│   ├── employee_routes.py
│   └── payraise_routes.py
├── requirements.txt
├── README.md
├── PROJECT_NOTES.md
├── .gitignore
├── static/
│   └── styles.css
└── templates/
    ├── addemployee.html
    ├── addpayraise.html
    ├── auditlog.html
    ├── base.html
    ├── changepassword.html
    ├── editemployee.html
    ├── home.html
    ├── listemployees.html
    ├── listpayraises.html
    ├── login.html
    ├── mypayraises.html
    ├── resetpassword.html
    ├── result.html
    ├── sendaddpayraisehmac.html
    ├── setup_admin.html
    └── submitdeletepayraise.html
```

## Local Files Not Committed to Git

The following local files and folders should stay private and should not be committed:

```text
.env
.venv/
EmployeeDB.db
backups/
__pycache__/
.idea/
```

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration purposes only.

The seeded demo accounts all use the password `test123`, and the application stores those passwords as hashes.

## Security Notice

This project demonstrates practical database security concepts for a local Flask application. It should not be used with real employee data unless the remaining limitations are understood and addressed, especially around long-term encryption key management, audit log review, backup protection, and deployment configuration.

## Author

Jeffrey Higi