"""
Database Backup Script

Creates a timestamped backup copy of the local SQLite database.
Backups are stored in the backups/ folder.
"""

import shutil
from datetime import datetime
from pathlib import Path


DB_NAME = "EmployeeDB.db"
BACKUP_DIR = "backups"


def backup_database():
    """Create a timestamped backup of the SQLite database file."""
    db_path = Path(DB_NAME)

    if not db_path.exists():
        print(f"Backup failed: {DB_NAME} does not exist.")
        print("Run init_db.py or reset_demo_db.py before creating a backup.")
        return

    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_dir / f"EmployeeDB_{timestamp}.db"

    shutil.copy2(db_path, backup_file)

    print("Database backup created successfully.")
    print(f"Backup file: {backup_file}")


if __name__ == "__main__":
    backup_database()