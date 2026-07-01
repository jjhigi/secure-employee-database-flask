"""
Database Initialization Script

Creates the local SQLite database tables for Flask Employee Manager if they do
not already exist. This script is safe to run multiple times and does not delete
existing data.
"""

import sqlite3

DB_NAME = "EmployeeDB.db"


def column_exists(cur, table_name, column_name):
    """Return True if a column exists in the given SQLite table."""
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]

    return column_name in columns


def create_tables():
    """Create or update the local database schema without deleting records."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS Employee
            (
                UserID        INTEGER PRIMARY KEY AUTOINCREMENT,
                Name          TEXT    NOT NULL,
                Age           INTEGER NOT NULL,
                PhNum         TEXT    NOT NULL,
                CurrentSalary TEXT,
                SecurityLevel INTEGER NOT NULL,
                PasswordHash  TEXT    NOT NULL,
                IsActive      INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS EmpPayRaise
            (
                PayRaiseID   INTEGER PRIMARY KEY AUTOINCREMENT,
                EmpID        INTEGER NOT NULL,
                PayRaiseDate TEXT    NOT NULL,
                RaiseAmt     TEXT    NOT NULL,
                IsVoided     INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (EmpID) REFERENCES Employee (UserID)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS AuditLog
            (
                AuditLogID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserID     INTEGER,
                Action     TEXT NOT NULL,
                Details    TEXT,
                CreatedAt  TEXT NOT NULL
            )
            """
        )

        if not column_exists(cur, "EmpPayRaise", "IsVoided"):
            cur.execute(
                """
                ALTER TABLE EmpPayRaise
                ADD COLUMN IsVoided INTEGER NOT NULL DEFAULT 0
                """
            )
            print("Added IsVoided column to EmpPayRaise.")

        if not column_exists(cur, "Employee", "CurrentSalary"):
            cur.execute(
                """
                ALTER TABLE Employee
                ADD COLUMN CurrentSalary TEXT
                """
            )
            print("Added CurrentSalary column to Employee.")

        conn.commit()

    print("Database initialized successfully.")
    print("Existing data was not deleted.")


if __name__ == "__main__":
    create_tables()
