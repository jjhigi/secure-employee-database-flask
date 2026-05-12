# Flask Employee Manager

A secure Flask web application for managing employee records and pay raise data with encrypted database storage, role-based access control, and encrypted socket communication.

## Tech Stack

- **Backend**: Python + Flask
- **Database**: SQLite
- **Encryption**: AES via PyCryptodome
- **Authentication**: Flask sessions
- **Authorization**: Role-based security levels
- **Networking**: Python sockets + TCP servers
- **Message Authentication**: HMAC with SHA3-512
- **Templates**: HTML + Jinja2

## Features

- User login system with encrypted credentials
- Role-based access control using employee security levels
- Add new employee records
- View employee records with decrypted sensitive fields
- Add and view pay raise records
- Show pay raises for the currently logged-in user
- Store sensitive employee and pay raise data using AES encryption
- Send encrypted socket messages to request pay raise deletion
- Send HMAC-authenticated encrypted socket messages to add pay raises
- Pre-seeded with sample employee and pay raise data for testing

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

Open http://127.0.0.1:5000 and sign in with a demo account:

- Username: `PDiana`
- Password: `test123`

Other seeded users also use:

- Password: `test123`

### Socket Servers

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

### Database Commands

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

- Flask handles routing, login, sessions, validation, and page rendering
- SQLite stores employee and pay raise records
- AES encryption protects sensitive stored values
- Role-based security levels control which pages users can access
- Socket servers demonstrate encrypted client/server communication
- HMAC validation helps verify that add-pay-raise messages were not tampered with

## Application Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET / POST | `/login` | No | Sign in with employee credentials |
| GET | `/logout` | Yes | Log out current user |
| GET | `/` | Yes | Home page with navigation links |
| GET | `/addemployee` | Yes, Level 1 | Show add employee form |
| POST | `/addrec` | Yes, Level 1 | Create a new employee |
| GET | `/listemployees` | Yes, Level 1 or 2 | List employee records |
| GET | `/listpayraises` | Yes, Level 2 | List all pay raise records |
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
└── templates/
    ├── addemployee.html
    ├── addpayraise.html
    ├── home.html
    ├── listemployees.html
    ├── listpayraises.html
    ├── login.html
    ├── mypayraises.html
    ├── result.html
    ├── sendaddpayraisehmac.html
    └── submitdeletepayraise.html
```

## Author

Jeffrey Higi