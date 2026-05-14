# Flask Employee Manager

A local-only Flask web application for managing employee records and pay raise data.

This project started as a class assignment and has been expanded into a more polished local database app with shared templates, styling, employee search, pay raise filtering, employee editing, employee deactivation/reactivation, admin password reset, password hashing, encrypted database fields, safer database setup scripts, and TCP socket messaging demos.

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

## Project Scope

This project is designed as a **local-only Flask application** that runs on the same PC as the SQLite database.

It is intended for:

- Local development
- Portfolio demonstration
- Small-scale record management practice
- Learning Flask, SQLite, authentication, authorization, encryption, and socket messaging

It is **not intended for public internet deployment** without additional security hardening.

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

### Security and Access Control

- User login system with Flask sessions
- Passwords stored using Werkzeug password hashing
- Role-based access control using employee security levels
- Selected employee and pay raise fields stored with AES encryption
- HMAC-authenticated encrypted socket message for pay raise creation
- Encrypted socket message for pay raise deletion

### Project Structure and Usability

- Shared Jinja base template for consistent layout
- CSS styling for navigation, forms, and tables
- Safer database setup scripts for initialization, demo seeding, and intentional resets
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
├── init_db.py
├── seed_demo.py
├── reset_demo_db.py
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

The seeded demo accounts all use the password `test123`, but the application stores those passwords as hashes rather than reversible encrypted values.

No real employee data should be stored in this project without additional security improvements.

## Security Notice

This project demonstrates several security concepts, including role-based access control, password hashing, encrypted database fields, encrypted socket messaging, and HMAC message authentication.

However, it is still a local educational/demo application. It is not production-ready without additional changes such as:

- Moving secrets and encryption keys out of source code
- CSRF protection for forms
- Stronger key and IV/nonce handling for encryption
- Debug mode disabled outside development
- More complete logging, backup, and account management controls

## Author

Jeffrey Higi