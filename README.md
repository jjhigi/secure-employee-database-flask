# Flask Employee Manager

A local-first Flask web application for managing employee records and pay raise data.

This project is meant as an exercise in **databases and database security**. It uses a small employee/pay-raise database to explore authentication, authorization, password hashing, encrypted fields, CSRF protection, local backups, safe restore, audit logging, protected form submissions, and authenticated socket messaging.

The end goal is a secure, usable **local employee database** that runs on a single admin computer. It is not intended to be enterprise HR software, public SaaS, or an intranet application.

## Tech Stack

- **Backend**: Python + Flask
- **Database**: SQLite
- **Templates**: HTML + Jinja2
- **Styling**: CSS
- **Authentication**: Flask sessions + Werkzeug password hashing
- **Authorization**: Role-based security levels
- **Encryption**: AES via PyCryptodome
- **Networking**: Python sockets + TCP servers
- **Message Authentication**: HMAC with SHA3-512
- **Form Protection**: Flask-WTF CSRF protection
- **Configuration**: python-dotenv environment configuration

## Security Features

- Passwords are stored using Werkzeug password hashing
- Employee passwords are never displayed in the application
- Logged-in users can change their own passwords after verifying their current password
- Admin users can reset employee passwords without viewing existing passwords
- Inactive employee accounts are blocked from logging in
- Role-based access control restricts pages by employee security level
- Protected pages re-check the logged-in session against the current database user
- Stale sessions are cleared when the database user no longer matches the session
- Selected employee and pay raise fields are stored with AES encryption using a random IV for each encrypted value
- Form submissions are protected with CSRF tokens using Flask-WTF
- Flask debug mode is controlled by an environment variable
- Flask secret key, AES settings, and HMAC secret are loaded from local environment configuration
- Session cookies are configured with `HttpOnly` and `SameSite=Lax`
- Local database backups can be created with a timestamped backup script
- Local database backups can be restored with a safety backup created first
- Sensitive account actions are recorded in a local audit log
- Encrypted TCP socket messages are used for pay raise deletion
- HMAC-authenticated encrypted TCP socket messages are used for pay raise creation

## Features

### Employee Management

- Create the first administrator account through an initial setup page when the database is empty
- Add, edit, search, deactivate, and reactivate employee records
- Search employees by name, user ID, security level, or active/inactive status
- View employee records without displaying passwords
- Reset employee passwords as an admin
- Change own password while logged in
- Block inactive employee accounts from logging in

### Pay Raise Management

- Add pay raise records directly through Flask
- View pay raise records
- Filter pay raise records by employee ID, date range, and minimum amount
- Show pay raises for the currently logged-in user
- Store pay raise amounts using AES encryption
- Submit encrypted socket-based pay raise deletion requests
- Submit encrypted and HMAC-authenticated socket-based pay raise creation requests

### Database Utilities

- Initialize database tables without deleting existing data
- Seed demo data for local testing
- Reset and rebuild the demo database intentionally
- Create timestamped local database backups
- Restore a database backup from the `backups/` folder
- Create a safety backup before restoring over the current database
- Record selected sensitive actions in the `AuditLog` table

## Security Features Still To Be Implemented

- Improve long-term AES key management and rotation
- Add more complete input validation and field length limits
- Improve error handling and user feedback
- Add deployment documentation for any future non-local use
- Replace the Flask development server with a production WSGI server if the project is ever adapted beyond local-only use

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Setup

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

Demo login:

```text
Username: PDiana
Password: test123
```

Other seeded demo users also use:

```text
Password: test123
```

## Initial Admin Setup

If the database has no employee records, create the first admin account at:

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

> **Warning:** `reset_demo_db.py` and `setup.py` delete existing Employee, EmpPayRaise, and AuditLog records before recreating the demo database. Use `init_db.py` for safer setup.

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

- Flask handles routing, login, sessions, validation, and page rendering.
- SQLite stores employee, pay raise, and audit log records locally.
- Passwords are stored as one-way hashes using Werkzeug password hashing.
- AES encryption is used for selected stored values, such as names, phone numbers, and pay raise amounts.
- Role-based security levels control which pages users can access.
- `AuditLog` records selected sensitive actions such as password changes, password resets, and employee activation changes.
- Socket servers demonstrate encrypted client/server communication.
- HMAC validation helps verify that add-pay-raise messages were not tampered with.

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
├── Encryption.py
├── ProcessPayRaiseDeletionsServer.py
├── AddAPayRaiseServer.py
├── requirements.txt
├── README.md
├── .gitignore
├── static/
│   └── styles.css
└── templates/
    ├── addemployee.html
    ├── addpayraise.html
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

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration purposes only.

The seeded demo accounts all use the password `test123`, and the application stores those passwords as hashes.

## Security Notice

This project demonstrates practical database security concepts for a local Flask application. It should not be used with real employee data unless the remaining limitations are understood and addressed, especially around long-term encryption key management, audit log review, backup protection, and deployment configuration.

## Author

Jeffrey Higi