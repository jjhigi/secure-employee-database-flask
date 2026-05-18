# Project Notes

## Current Goal

Flask Employee Manager is being developed as a very secure, usable, portable local employee database for one admin computer.

The goal is not to build an enterprise HR system, public SaaS app, or intranet application. The intended user is closer to a small business owner who needs a simple local employee/pay raise tracking tool with strong local security and minimal setup.

## Current Architecture

- Python + Flask web app
- SQLite local database
- Server-rendered Jinja templates
- CSS styling in `static/styles.css`
- Local `.env` configuration loaded through `config.py`
- Database stored locally as `EmployeeDB.db`
- Demo/test data can be seeded with `seed_demo.py`
- Database can be backed up with `backup_db.py`

## Current Security Features

- Passwords are stored using Werkzeug password hashing
- Employee passwords are never displayed
- Admin users can reset employee passwords
- Inactive employee accounts cannot log in
- Role-based access control using security levels
- CSRF protection through Flask-WTF
- Flask debug mode controlled by environment config
- Flask secret key, AES settings, and HMAC secret loaded from `.env`
- Session cookies configured with `HttpOnly` and `SameSite=Lax`
- Sensitive fields such as employee names, phone numbers, and pay raise amounts are encrypted
- Safer database scripts separate initialization, demo seeding, reset, and backup

## Important Design Decisions

- Keep the app local-first and single-computer focused.
- Do not optimize for public deployment or intranet deployment right now.
- Do not ask the end user to manually understand secrets long-term; future setup should automate local config generation.
- `.env` is private and should not be committed.
- `.env.example` is safe to commit as a template.
- Passwords are hashed, not encrypted.
- Employee/pay raise fields that must be displayed later are encrypted and decrypted by the app.
- The socket/HMAC workflow exists currently, but may not fit the final usability goal. Future decision needed: remove it from the main app or archive it.

## Current Open Questions

- Should socket/HMAC routes be removed from the main app?
- Should pay raise deletion become a direct Flask route instead?
- Should pay raises be soft-deleted/voided instead of deleted?
- Should the app be refactored into Flask Blueprints later?

## Planned Roadmap

1. Add database restore support with `restore_db.py`
2. Add first-admin setup flow
3. Add logged-in user password change
4. Add audit logging for sensitive actions
5. Improve validation and field length limits
6. Replace raw security level numbers with role labels/dropdowns
7. Add active/inactive employee filtering
8. Add pay raise void/deactivation
9. Improve AES IV/nonce handling
10. Add `setup_local_config.py` to generate `.env`
11. Add `setup.bat` and `run.bat`
12. Later: split `app.py` into Blueprints
13. Much later: optional executable/installer packaging

## Git Workflow

- Work from clean `main`
- Create one branch per feature
- Test locally before committing
- Use clear commit messages
- Open PRs and merge into `main`
- Delete branches after merge