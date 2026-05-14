# Flask Employee Manager

A local-only Flask web application for managing employee records and pay raise data.

This project started as a class assignment and has been expanded into a more polished local database app with shared templates, styling, employee search, pay raise filtering, employee editing, role-based access control, encrypted database fields, and TCP socket messaging demos.

## Tech Stack

- **Backend**: Python + Flask
- **Database**: SQLite
- **Templates**: HTML + Jinja2
- **Styling**: CSS
- **Authentication**: Flask sessions
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

- User login system with Flask sessions
- Role-based access control using employee security levels
- Add new employee records
- Edit existing employee records
- Search employees by name, user ID, or security level
- View employee records without displaying passwords
- Add and view pay raise records
- Filter pay raise records by employee ID, date range, and minimum amount
- Show pay raises for the currently logged-in user
- Store selected employee and pay raise fields using AES encryption
- Send encrypted socket messages to request pay raise deletion
- Send HMAC-authenticated encrypted socket messages to add pay raises
- Shared Jinja base template for consistent layout
- Basic CSS styling for navigation, forms, and tables
- Pre-seeded with sample employee and pay raise data for local testing

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment on Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create and seed the SQLite database
python setup.py
```

### Running

Start the Flask application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Sign in with a demo account:

- Username: `PDiana`
- Password: `test123`

Other seeded users also use:

- Password: `test123`

## Socket Server Features

Some features require separate TCP servers to be running.

Start the pay raise deletion server in a separate terminal:

```bash
python ProcessPayRaiseDeletionsServer.py
```

Start the authenticated add-pay-raise server in another separate terminal:

```bash
python AddAPayRaiseServer.py
```

For full functionality, run all three processes at the same time:

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
# Create or rebuild the database with sample data
python setup.py

# Start the Flask application
python app.py

# Start encrypted delete-message server
python ProcessPayRaiseDeletionsServer.py

# Start HMAC-authenticated add-message server
python AddAPayRaiseServer.py
```

> **Note:** Running `setup.py` rebuilds the demo database. Any records added while testing will be erased.

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
- AES encryption is used for selected stored values.
- Role-based security levels control which pages users can access.
- Socket servers demonstrate encrypted client/server communication.
- HMAC validation helps verify that add-pay-raise messages were not tampered with.

## Application Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET / POST | `/login` | No | Sign in with employee credentials |
| GET | `/logout` | Yes | Log out current user |
| GET | `/` | Yes | Home page with navigation links |
| GET | `/addemployee` | Yes, Level 1 | Show add employee form |
| POST | `/addrec` | Yes, Level 1 | Create a new employee |
| GET | `/listemployees` | Yes, Level 1 or 2 | List and search employee records |
| GET / POST | `/editemployee/<user_id>` | Yes, Level 1 | Edit an employee record |
| GET | `/listpayraises` | Yes, Level 2 | List and filter all pay raise records |
| GET | `/mypayraises` | Yes | Show current user's pay raises |
| GET / POST | `/addpayraise` | Yes | Add pay raise directly through Flask |
| GET / POST | `/submitdeletepayraise` | Yes, Level 1 or 2 | Send encrypted delete request to TCP server |
| GET / POST | `/sendaddpayraisehmac` | Yes | Send encrypted and authenticated add-pay-raise message |

## Project Structure

```text
flask-employee-manager/
├── app.py
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
    ├── result.html
    ├── sendaddpayraisehmac.html
    └── submitdeletepayraise.html
```

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration purposes only. The setup script creates a local SQLite database and seeds it with fake employee data for testing.

No real employee data should be stored in this project without additional security improvements.

## Security Notice

This project demonstrates several security concepts, including role-based access control, encrypted database fields, encrypted socket messaging, and HMAC message authentication.

However, it is still a local educational/demo application. It is not production-ready without additional changes such as:

- Password hashing instead of reversible password encryption
- Moving secrets and encryption keys out of source code
- CSRF protection for forms
- Safer database setup scripts that do not reset data accidentally
- Stronger key and IV/nonce handling for encryption
- Debug mode disabled outside development
- More complete logging, backup, and account management controls

## Author

Jeffrey Higi