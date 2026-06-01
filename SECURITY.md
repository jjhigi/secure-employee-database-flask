# Security Notes

This document explains the main security design decisions in Flask Employee Manager.

The app is designed as a local-first employee/pay raise database for one admin computer. It is not intended for public internet deployment, SaaS use, or enterprise HR use.

## Intended Use

Flask Employee Manager is intended to run locally on one trusted admin computer.

Expected use:

- The app runs on `127.0.0.1`
- The database is stored locally as `EmployeeDB.db`
- One local admin computer controls setup, backups, and restore
- The browser UI is used locally
- The terminal running the Flask server stays open while the app is in use

## Authentication

- Users log in with employee credentials.
- Passwords are stored with Werkzeug password hashing.
- Plaintext passwords are never stored.
- Plaintext passwords are never displayed.
- Logged-in users can change their own passwords.
- Password changes require the current password.
- Admin users can reset employee passwords without viewing existing passwords.
- Inactive employee accounts cannot log in.

## Session Protection

Sessions are checked against the current database state.

On protected routes, the app verifies that:

- The session has a `UserID`
- The database user still exists
- The account is still active
- The session password hash still matches the current stored password hash

If the database user no longer exists, the account is inactive, or the password hash no longer matches, the session is cleared and the user must log in again.

Session cookies are configured with:

- `HttpOnly`
- `SameSite=Lax`

## First Admin Setup

The first admin setup page is only available when the `Employee` table is empty.

Behavior:

- `/` redirects to `/setup-admin` when there are no employee records
- `/setup-admin` creates the first Level 1 admin account
- After the first employee account exists, `/setup-admin` is blocked

This prevents repeated first-admin creation after the app has been initialized.

## Role-Based Access Control

The app uses numeric security levels for authorization.

| Level | Role | Main Permissions |
|-------|------|------------------|
| 1 | Admin | Manage employees, reset passwords, deactivate/reactivate accounts, view audit logs, list all pay raises, and void pay raises |
| 2 | Manager | List employees, list all pay raises, and void pay raises |
| 3 | Employee | View own pay raises, add own pay raises, and change own password |

Access control is centralized through `auth_helpers.py`.

Unauthorized protected pages use the app's existing 404 behavior instead of exposing extra permission details.

## Employee Account Controls

Admin users can:

- Add employees
- Edit employee records
- Reset employee passwords
- Deactivate employee accounts
- Reactivate employee accounts
- View audit logs

Admin users cannot deactivate their own account.

Level 2 manager users can list employees, but they cannot edit employees, reset passwords, deactivate accounts, reactivate accounts, or view audit logs.

## Encryption at Rest

Selected employee and pay raise fields are encrypted before storage.

Encrypted fields include:

- Employee name
- Employee phone number
- Pay raise amount

Encryption is handled through shared helpers in `crypto_helpers.py`, which call the AES helper in `Encryption.py`.

AES behavior:

- Uses AES through PyCryptodome
- Uses CFB mode
- Uses a new random IV for each encrypted value
- Stores encrypted values as base64-encoded `IV + ciphertext`

## CSRF Protection

Form submissions are protected with Flask-WTF CSRF protection.

Templates include CSRF tokens for protected POST forms, including:

- Add employee
- Edit employee
- Reset password
- Deactivate/reactivate employee
- Add pay raise
- Void pay raise request
- HMAC add pay raise request
- Change password
- First admin setup

## Validation

The app validates user input before database changes.

Examples:

- Employee names cannot be blank or exceed the configured limit
- Ages must be within the allowed range
- Phone numbers cannot be blank or exceed the configured limit
- Passwords must meet configured length limits
- Security levels must be valid known roles
- Pay raise amounts must be numeric, greater than zero, and below the configured maximum
- Pay raise dates must be valid dates within the allowed range
- User IDs and employee IDs must be numeric where required

Shared validation limits are stored in `validation_constants.py`.

## Audit Logging

Sensitive account actions are written to the `AuditLog` table.

Audit log entries include:

- User ID
- Action
- Details
- Timestamp

Examples of audited actions:

- User changes their own password
- Admin resets an employee password
- Admin deactivates an employee account
- Admin reactivates an employee account
- Admin changes an employee security level
- Admin or manager sends a pay raise void request

Admin users can view and filter audit log entries by:

- Action
- User ID
- Start date
- End date
- Details text

Audit log filtering uses parameterized SQL.

## Pay Raise Voiding

Pay raise records are voided instead of permanently deleted.

Voided pay raises:

- Remain visible in the full pay raise list
- Show a `Voided` status
- Are hidden from the current user's personal pay raise page
- Cannot be voided again as active records

## Socket Messaging

Some pay raise actions use local TCP socket servers.

Socket workflows:

- Encrypted pay raise void request
- Encrypted and HMAC-authenticated pay raise creation request

The HMAC add-pay-raise workflow:

- Builds a plaintext message body
- Encrypts the message body
- Signs the plaintext body with HMAC-SHA3-512
- Sends ciphertext plus HMAC tag to the local socket server
- Server decrypts the message
- Server verifies the HMAC tag
- Server validates fields before inserting the record

HMAC verification uses `hmac.compare_digest()`.

## Local Configuration

Configuration is loaded from environment variables or a local `.env` file through `config.py`.

Required secrets:

- `FLASK_SECRET_KEY`
- `HMAC_SECRET`
- `AES_KEY`

`AES_KEY` must be 16, 24, or 32 characters after UTF-8 encoding.

The real `.env` file should not be committed to GitHub.

## Files Excluded from Git

The following should stay local and private:

```text
.env
.venv/
EmployeeDB.db
backups/
__pycache__/
.idea/
PROJECT_NOTES.md
```

## Backup and Restore

Backups can be created with:

```bash
python backup_db.py
```

Restores can be performed with:

```bash
python restore_db.py EmployeeDB_YYYY-MM-DD_HH-MM-SS.db
```

Restore behavior:

- Backup file must be inside the `backups/` folder
- Backup file must be a `.db` file
- Backup file must pass SQLite validation
- A safety backup of the current database is created before restore

Backup files should be protected by the local computer/user.

## Safe Initialization vs. Demo Reset

Safe initialization:

```bash
python init_db.py
```

This creates missing tables and applies safe schema updates without deleting existing data.

Demo seeding:

```bash
python seed_demo.py
```

This inserts demo data only when the database is empty.

Intentional demo reset:

```bash
python reset_demo_db.py
```

This deletes and rebuilds demo tables.

Backward-compatible reset:

```bash
python setup.py
```

This also resets demo data and should not be used for safe setup.

## Future Security Improvements

Possible future improvements:

- Optional Waitress-based local server runner
- Better `.env` generation during setup
- Optional audit log export
- Key rotation plan for encrypted fields
- Packaged desktop-style launcher
- More user-friendly backup and restore interface