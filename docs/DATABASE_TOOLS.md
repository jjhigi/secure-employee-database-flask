# Database Tools

This project uses a local SQLite database named:

```text
EmployeeDB.db
```

The database is stored locally on the computer running the app.

## Safe Database Initialization

To safely create database tables without deleting existing data:

```bat
.venv\Scripts\python.exe init_db.py
```

Use this when the database file is missing or when you need to make sure the required tables exist.

This does not intentionally delete existing records.

## Reset to First Admin Setup

To return to the first-admin setup flow:

1. Stop the Flask app.
2. Delete the local database file:

```text
EmployeeDB.db
```

3. Recreate the empty database tables:

```bat
.venv\Scripts\python.exe init_db.py
```

4. Start the app again:

```bat
run.bat
```

If the Employee table is empty, the app redirects to:

```text
/setup-admin
```

Do not delete `.env` or `.venv` for this reset. Only delete `EmployeeDB.db`.

## Add Demo Data

To add demo data to an empty database:

```bat
.venv\Scripts\python.exe seed_demo.py
```

If demo data is seeded, the sample users use:

```text
Password: test123
```

Example demo login:

```text
Username: PDiana
Password: test123
```

## Reset Demo Database

To intentionally reset and rebuild the demo database:

```bat
.venv\Scripts\python.exe reset_demo_db.py
```

Warning: this deletes existing `Employee`, `EmpPayRaise`, and `AuditLog` records before recreating demo data.

Use this only for local testing or demonstration.

## Create a Backup

To create a timestamped backup:

```bat
.venv\Scripts\python.exe backup_db.py
```

Backups are stored in:

```text
backups/
```

To list backups:

```bat
dir backups
```

Backup filenames look like:

```text
EmployeeDB_YYYY-MM-DD_HH-MM-SS.db
```

## Restore from Backup

To restore from a backup, provide the backup filename:

```bat
.venv\Scripts\python.exe restore_db.py backups\EmployeeDB_YYYY-MM-DD_HH-MM-SS.db
```

Example:

```bat
.venv\Scripts\python.exe restore_db.py backups\EmployeeDB_2026-05-17_12-00-00.db
```

The restore script creates a safety backup of the current database before replacing it.

Safety backup filenames may look like:

```text
EmployeeDB_before_restore_YYYY-MM-DD_HH-MM-SS.db
```

These files are created so you can recover the database state from right before a restore.

Avoid choosing this unless you specifically want to undo a restore:

```text
EmployeeDB_before_restore_
```

## Common Database Commands

```bat
.venv\Scripts\python.exe init_db.py
.venv\Scripts\python.exe seed_demo.py
.venv\Scripts\python.exe backup_db.py
.venv\Scripts\python.exe restore_db.py backups\EmployeeDB_YYYY-MM-DD_HH-MM-SS.db
.venv\Scripts\python.exe reset_demo_db.py
```

## Backup Safety

Backup files contain local database data.

Protect the `backups/` folder the same way you protect the main database file.
