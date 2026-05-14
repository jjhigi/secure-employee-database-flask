"""
Database Initialization Script

Creates the local SQLite database tables for Flask Employee Manager if they
do not already exist. This script does not delete existing data.
"""

import sqlite3


DB_NAME = "EmployeeDB.db"


def create_tables():
    """Create Employee and EmpPayRaise tables if they do not already exist."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Employee(
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Age INTEGER NOT NULL,
            PhNum TEXT NOT NULL,
            SecurityLevel INTEGER NOT NULL,
            PasswordHash TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS EmpPayRaise(
            PayRaiseID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmpID INTEGER NOT NULL,
            PayRaiseDate TEXT NOT NULL,
            RaiseAmt TEXT NOT NULL,
            FOREIGN KEY (EmpID) REFERENCES Employee(UserID)
        )
        """
    )

    conn.commit()
    conn.close()

    print("Database initialized successfully.")
    print("Existing data was not deleted.")


if __name__ == "__main__":
    create_tables()