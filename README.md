# Flask Employee Manager

A local-first Flask web application for managing employee records and pay raise data.

This project demonstrates practical database security concepts in a small local employee/pay-raise database, including authentication, role-based authorization, password hashing, encrypted fields, CSRF protection, validation, backups, safe restore, audit logging, and authenticated socket messaging.

The goal is a secure, usable local database that runs on one admin computer with minimal setup. It is not intended to be an enterprise HR system, public web app, SaaS app, or intranet app.

## Tech Stack

* **Backend:** Python, Flask
* **Database:** SQLite
* **Templates:** Jinja2 server-rendered HTML
* **Styling:** CSS
* **Authentication:** Flask sessions, Werkzeug password hashing
* **Authorization:** Role-based security levels
* **Encryption:** AES through PyCryptodome
* **Message Authentication:** HMAC with SHA3-512
* **Form Protection:** Flask-WTF CSRF protection
* **Configuration:** Local `.env` file loaded through `config.py`

## Main Features

* Create the first admin account when the database is empty
* Add, edit, list, search, deactivate, and reactivate employees
* Reset employee passwords as an admin
* Change your own password while logged in
* Store employee passwords as hashes, never plaintext
* Encrypt selected employee and pay raise fields at rest
* Track encrypted current salary for each employee
* List and filter pay raise records by role
* Let admins and managers submit socket-based encrypted and HMAC-authenticated pay raise void requests
* Let admins and managers submit socket-based encrypted and HMAC-authenticated pay raise creation requests
* Update current salary atomically when pay raises are added or voided
* Create timestamped local database backups
* Restore from backup with a safety backup created first
* Reset and rebuild demo data for testing
* Record selected sensitive actions in an audit log

## Security Highlights

* Passwords are stored with Werkzeug password hashing.
* Passwords are never displayed back to users.
* Role-based access control protects employee, pay raise, and audit routes.
* Sessions are revalidated against the current database user, active status, and stored password hash.
* Inactive accounts cannot log in.
* First-admin setup is only available when the database is empty.
* Selected employee and pay raise fields are encrypted at rest using AES with a random IV per encrypted value.
* CSRF protection is enabled through Flask-WTF.
* Session cookies use `HttpOnly` and `SameSite=Lax`.
* Sensitive account actions are written to the `AuditLog` table.
* Pay raise records are voided instead of permanently deleted.
* HMAC validation helps detect tampered pay raise socket messages.
* Local secrets, databases, backups, virtual environments, IDE files, and project notes are excluded from Git.

More detailed security notes are documented in `SECURITY.md`.

## Security Levels

| Level | Role     | Main Permissions                                                                                                             |
| ----- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 1     | Admin    | Manage employees and salaries, reset passwords, deactivate/reactivate accounts, view audit logs, list all pay raises, add pay raises, and void pay raises |
| 2     | Manager  | List employees and salaries, list all pay raises, add pay raises, and void pay raises |
| 3     | Employee | View own current salary and pay raises, and change own password |

## Quick Start

Download the ZIP from GitHub, extract it, and open the extracted project folder.

Run:

```bat
setup.bat
```

Then run:

```bat
run.bat
```

The app opens at:

```text
http://127.0.0.1:5000
```

On first launch, if the database has no employee records, the app redirects to the initial admin setup page. Create the first admin account there, then log in normally.

For detailed Windows setup and troubleshooting, see:

```text
docs/WINDOWS_SETUP.md
```

## Documentation

* `docs/WINDOWS_SETUP.md` — Windows setup, running the app, Smart App Control, and PowerShell notes
* `docs/DATABASE_TOOLS.md` — database initialization, backup, restore, demo reset, and first-admin reset
* `SECURITY.md` — security design notes

## Socket Server Features

Some pay raise features use separate local TCP socket servers.

Successful pay raise creation increases the employee's current salary in the
same database transaction. Voiding an active raise subtracts its amount once
and marks the record voided in the same transaction.

For full socket functionality, run all three processes at the same time:

```bat
run.bat
```

```bat
.venv\Scripts\python.exe ProcessPayRaiseDeletionsServer.py
```

```bat
.venv\Scripts\python.exe AddAPayRaiseServer.py
```

## Demo Data Notice

This project uses sample employee and pay raise records for demonstration only. Demo accounts use the password `test123`, stored as a hash.

## Author

Jeffrey Higi
