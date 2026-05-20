# Project Notes

## Current Goal

Flask Employee Manager is being developed as a secure, usable, portable local employee database for one admin computer.

The goal is not to build an enterprise HR system, public SaaS app, public web app, or intranet application. The intended user is closer to a small business owner or local admin user who needs a simple employee/pay raise tracking tool with strong local security and minimal setup.

## Current Architecture

- Python + Flask web app
- SQLite local database
- Flask Blueprints
- Server-rendered Jinja templates
- CSS styling in `static/styles.css`
- Local `.env` configuration loaded through `config.py`
- Database stored locally as `EmployeeDB.db`
- Database setup, demo seeding, reset, backup, and restore are handled by separate scripts
- Windows setup/run scripts are included for easier local use

## Main App Structure

- `app.py` handles app setup, CSRF setup, Blueprint registration, and startup
- `routes/auth_routes.py` handles `/`, `/setup-admin`, `/login`, `/logout`, and `/changepassword`
- `routes/employee_routes.py` handles employee/admin/audit log routes
- `routes/payraise_routes.py` handles pay raise routes and socket-submit routes
- `auth_helpers.py` contains shared access-control helpers
- `crypto_helpers.py` contains shared `enc()` and `dec()` helpers
- `validation_constants.py` contains shared field limits
- `db.py` contains `get_db()`
- `audit.py` contains `log_audit()`

## Current Security Features

- Passwords are stored using Werkzeug password hashing
- Employee passwords are never displayed
- Logged-in users can change their own passwords
- Password changes require the current password
- Admin users can reset employee passwords
- Inactive employee accounts cannot log in
- Admin users can deactivate and reactivate employee accounts
- Admin users cannot deactivate their own account
- First-admin setup is available only when the `Employee` table is empty
- `/` redirects to `/setup-admin` when the database has no employee records
- `/setup-admin` is blocked after the first employee account exists
- Role-based access control uses employee security levels
- Unauthorized protected pages use the app's existing 404 behavior
- Sessions are checked against the current database user and password hash
- Stale sessions are cleared when the database user/password hash no longer matches
- Selected employee and pay raise fields are encrypted at rest
- AES encryption uses a random IV for each encrypted value
- Shared encryption helpers are centralized in `crypto_helpers.py`
- CSRF protection is enabled through Flask-WTF
- Session cookies use `HttpOnly` and `SameSite=Lax`
- Flask debug mode is controlled by local environment configuration
- Flask secret key, AES secret, and HMAC secret are loaded from `.env`
- `.env`, the local database, backups, virtual environments, IDE files, and cache folders are excluded from Git
- Database initialization can create missing tables without deleting existing data
- Demo reset scripts are separated from safe initialization scripts
- Local backups can be created with `backup_db.py`
- Local backups can be restored with `restore_db.py`
- Restore creates a safety backup before replacing the current database
- Sensitive account actions are written to the `AuditLog` table
- Admin users can view and filter audit log entries
- Audit log filters use parameterized SQL
- Pay raise amount validation rejects blank, non-numeric, zero, negative, and oversized values
- Pay raise date validation rejects blank, invalid, too-old, and future dates
- Encrypted TCP socket messages are used for pay raise deletion requests
- HMAC-authenticated encrypted TCP socket messages are used for pay raise creation requests
- HMAC validation helps detect tampered add-pay-raise socket messages

## Database Scripts

- `init_db.py` safely creates missing database tables without deleting existing data
- `seed_demo.py` adds demo data for local testing
- `reset_demo_db.py` intentionally resets and rebuilds the demo database
- `setup.py` remains as a backward-compatible reset/demo command
- `backup_db.py` creates timestamped local backups
- `restore_db.py` restores a selected backup and creates a safety backup first

## Local Setup Scripts

- `setup.bat` prepares the local project on Windows
- `setup.bat` creates the virtual environment if needed
- `setup.bat` installs dependencies from `requirements.txt`
- `setup.bat` creates `.env` from `.env.example` if needed
- `setup.bat` runs safe database initialization
- `run.bat` activates the virtual environment
- `run.bat` opens the app in the browser
- `run.bat` starts the Flask app

## Important Design Decisions

- Keep the app local-first and single-computer focused
- Do not optimize for public deployment, SaaS deployment, or intranet deployment
- Prefer simple local setup over complex infrastructure
- Prefer small, testable changes
- Preserve current functionality unless intentionally changing it
- Keep security-related logic centralized where practical
- Keep database setup, demo data, reset, backup, and restore as separate scripts
- Keep `.env` private and commit only `.env.example`
- Hash passwords instead of encrypting them
- Encrypt fields that must be decrypted and displayed later
- Keep the browser-based Flask UI because it is simpler than building a native desktop UI
- Treat socket/HMAC features as part of the current assignment/demo design, but not necessarily ideal for the final usability goal

## Current Open Questions

- Should socket/HMAC routes remain part of the main app long-term?
- Should pay raise deletion become a direct Flask route instead of a socket workflow?
- Should pay raises be soft-deleted, voided, or archived instead of deleted?
- Should security level numbers be replaced with clearer role labels in the UI?
- Should local `.env` generation be automated more completely?
- Should the project eventually be packaged as an executable or installer?

## Completed Roadmap Items

- Split Flask app into Blueprints
- Added shared database helper with `get_db()`
- Added shared authorization helpers
- Added shared encryption helpers
- Added shared validation constants
- Added first-admin setup flow
- Added automatic redirect from `/` to `/setup-admin` when the database is empty
- Added logged-in user password change
- Added admin password reset
- Added inactive account login blocking
- Added account deactivation/reactivation
- Added audit logging for sensitive account actions
- Added audit log viewer
- Added audit log filtering
- Improved employee search
- Improved pay raise filtering
- Improved pay raise validation
- Improved AES IV handling with random IVs per encrypted value
- Added safe database initialization script
- Added demo seed script
- Added intentional reset/demo rebuild script
- Added backup script
- Added restore script with safety backup
- Added setup and run batch scripts
- Updated README setup/run documentation

## Remaining Roadmap

1. Replace raw security level numbers with clearer role labels/dropdowns
2. Consider soft-delete or void behavior for pay raises
3. Decide whether socket/HMAC workflows should stay in the main app
4. Add stronger local `.env` generation or setup automation
5. Improve UI wording and form layout where useful
6. Add more user-friendly error messages where needed
7. Consider packaging later as an optional executable/installer

## Git Workflow

- Work from clean `main`
- Create one branch per feature
- Keep each branch small and focused
- Test locally before committing
- Use clear commit messages
- Open PRs and merge into `main`
- Delete branches after merge
- Do not commit `.env`, `.venv`, `EmployeeDB.db`, backups, `__pycache__`, `.idea`, or temporary test files