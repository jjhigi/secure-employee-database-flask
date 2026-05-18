# Flask Employee Manager

A Flask web application for managing employee records and pay raise data.

This project is meant as an exercise in **databases and database security**. It uses a small employee/pay-raise database to explore authentication, authorization, password hashing, encrypted fields, CSRF protection, local database backups, safer database setup, protected form submissions, and authenticated socket messaging.

The end goal is a very secure **local employee database** that runs on a single admin computer. It is not intended to be enterprise HR software or a public internet-facing application, but it is being developed with practical local security and usability in mind.

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

## Current Security Features

- Passwords are stored using Werkzeug password hashing
- Employee passwords are never displayed in the application
- Admin users can reset employee passwords without viewing existing passwords
- Inactive employee accounts are blocked from logging in
- Role-based access control restricts pages by employee security level
- Selected employee and pay raise fields are stored with AES encryption
- Form submissions are protected with CSRF tokens using Flask-WTF
- Flask debug mode is controlled by an environment variable
- Flask secret key, AES settings, and HMAC secret are loaded from local environment configuration
- Session cookies are configured with `HttpOnly` and `SameSite=Lax`
- Database setup scripts separate initialization, demo seeding, and intentional resets
- Local database backups can be created with a timestamped backup script
- Encrypted TCP socket messages are used for pay raise deletion
- HMAC-authenticated encrypted TCP socket messages are used for pay raise creation
- Local database backups can be restored with a safety backup created first

## Security Features Still To Be Implemented

- Improve AES key and IV/nonce handling
- Add password change support for logged-in users
- Add audit logging for administrative actions
- Improve error handling and user feedback
- Add more complete input validation and field length limits
- Add deployment documentation for any future non-local use
- Replace the Flask development server with a production WSGI server if the project is ever adapted beyond local-only use

## Features

### Employee Management

- Add new employee records
- Edit existing employee records
- Search employees by name, user ID, security level, or active/inactive status
- View employee records without displaying passwords
- Deactivate and reactivate employee accounts instead of deleting records
- Block inactive employee accounts from logging in
- Reset employee passwords as an admin using hashed password storage

### Pay Raise Management

- Add pay raise records directly through Flask
- View pay raise records
- Filter pay raise records by employee ID, date range, and minimum amount
- Show pay raises for the currently logged-in user
- Store pay raise amounts using AES encryption

### Project Structure and Usability

- Shared Jinja base template for consistent layout
- CSS styling for navigation, forms, and tables
- Safer database setup scripts for initialization, demo seeding, and intentional resets
- Timestamped local database backup script
- Demo data available for local testing

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

## Running the App

Start the Flask application:

```bash
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

Demo login:

- Username: `PDiana`
- Password: `test123`

Other seeded users also use:

- Password: `test123`

## Socket Server Features

Some features require separate TCP servers to be running.

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

For full socket functionality, run all three processes at the same time:

```bash
# Terminal 1
python app.py

# Terminal 2
python ProcessPayRaiseDeletionsServer.py

# Terminal 3
python AddAPayRaiseServer.py
```

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

> **Warning:** `reset_demo_db.py` and `setup.py` delete existing Employee and EmpPayRaise records before recreating the demo database. Use `init_db.py` for safer setup.

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
- SQLite stores employee and pay raise records locally.
- Passwords are stored as one-way hashes using Werkzeug password hashing.
- AES encryption is used for selected stored values, such as names, phone numbers, and pay raise amounts.
- Role-based security levels control which pages users can access.
- Socket servers demonstrate encrypted client/server communication.
- HMAC validation helps verify that add-pay-raise messages were not tampered with.

## Application Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET / POST | `/login` | No | Sign in with employee credentials |
| GET | `/logout` | Yes | Log out current user |
| GET | `/` | Yes | Home page with navigation links |
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
    ├── editemployee.html
    ├── home.html
    ├── listemployees.html
    ├── listpayraises.html
    ├── login.html
    ├── mypayraises.html
    ├── resetpassword.html
    ├── result.html
    ├── sendaddpayraisehmac.html
    └── submitdeletepayraise.html
```

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration purposes only. The demo seed script creates fake employee data for local testing.

The seeded demo accounts all use the password `test123`, and the application stores those passwords as hashes.

## Security Notice

This project demonstrates practical database security concepts for a local Flask application. It should not be used with real employee data unless the remaining limitations are understood and addressed, especially around encryption key handling, backup restoration, audit logging, input validation, and deployment configuration.

## Author

Jeffrey Higi