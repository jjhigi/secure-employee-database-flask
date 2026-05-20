"""
Database Restore Script

Restores the local SQLite database from a .db backup file stored in the
backups/ folder.

Before restoring, this script creates a safety backup of the current
EmployeeDB.db file.
"""

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_NAME = "EmployeeDB.db"
BACKUP_DIR = "backups"


def is_valid_sqlite_database(db_path: Path) -> bool:
    """Return True if the file can be opened as a valid SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA quick_check")
        result = cur.fetchone()
        conn.close()

        return result is not None and result[0] == "ok"
    except sqlite3.Error:
        return False


def get_backup_path(backup_name: str) -> Path:
    """Get a safe backup path inside the backups folder."""
    backup_dir = Path(BACKUP_DIR).resolve()

    # Allow either:
    #   python restore_db.py EmployeeDB_2026-05-17_12-00-00.db
    # or:
    #   python restore_db.py backups/EmployeeDB_2026-05-17_12-00-00.db
    requested_path = Path(backup_name)

    if requested_path.parent == Path("."):
        backup_path = backup_dir / requested_path.name
    else:
        backup_path = requested_path.resolve()

    # Make sure the final path is still inside backups/
    try:
        backup_path.relative_to(backup_dir)
    except ValueError:
        raise ValueError("Restore failed: backup file must be inside the backups/ folder.")

    return backup_path


def restore_database(backup_name: str):
    """Restore EmployeeDB.db from a selected backup file."""
    db_path = Path(DB_NAME)
    backup_dir = Path(BACKUP_DIR)
    backup_path = get_backup_path(backup_name)

    print("Database restore started.")
    print(f"Requested backup: {backup_path}")

    if not backup_dir.exists():
        print(f"Restore failed: {BACKUP_DIR}/ folder does not exist.")
        print("Run backup_db.py first to create a backup.")
        return

    if not backup_path.exists():
        print("Restore failed: backup file was not found.")
        return

    if not backup_path.is_file():
        print("Restore failed: selected backup is not a file.")
        return

    if backup_path.suffix.lower() != ".db":
        print("Restore failed: only .db backup files can be restored.")
        return

    if not is_valid_sqlite_database(backup_path):
        print("Restore failed: selected file is not a valid SQLite database.")
        return

    backup_dir.mkdir(exist_ok=True)

    if db_path.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safety_backup = backup_dir / f"EmployeeDB_before_restore_{timestamp}.db"

        shutil.copy2(db_path, safety_backup)

        print("Safety backup created successfully.")
        print(f"Safety backup file: {safety_backup}")
    else:
        print(f"Warning: {DB_NAME} does not exist.")
        print("No safety backup was created because there was no current database.")

    shutil.copy2(backup_path, db_path)

    print("Database restored successfully.")
    print(f"Restored from: {backup_path}")
    print(f"Current database: {db_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  python restore_db.py <backup-file-name>")
        print()
        print("Example:")
        print("  python restore_db.py EmployeeDB_2026-05-17_12-00-00.db")
        print("  python restore_db.py backups/EmployeeDB_2026-05-17_12-00-00.db")
    else:
        try:
            restore_database(sys.argv[1])
        except ValueError as e:
            print(e)
