"""
Reset Demo Database Script

Deletes and recreates the local SQLite demo database tables, then inserts
sample employee and pay raise records for local testing.

Warning: Running this script removes existing Employee and EmpPayRaise data.
"""

import sqlite3
import Encryption
from werkzeug.security import generate_password_hash

DB_NAME = "EmployeeDB.db"


def enc(s: str) -> str:
    """Encrypt a Python string and return text for storage."""
    return Encryption.cipher.encrypt(s.encode("utf-8")).decode("utf-8")


def dec(s: str) -> str:
    """Decrypt text from SQLite back into a normal Python string."""
    return Encryption.cipher.decrypt(s)


def reset_demo_database():
    """Drop, recreate, and seed the demo database."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    try:
        cur.execute("DROP TABLE IF EXISTS AuditLog")
        cur.execute("DROP TABLE IF EXISTS EmpPayRaise")
        cur.execute("DROP TABLE IF EXISTS Employee")
        conn.commit()
        print("AuditLog table dropped.")
        print("EmpPayRaise table dropped.")
        print("Employee table dropped.")
    except Exception:
        print("Tables did not exist.")

    cur.execute(
        """
        CREATE TABLE Employee
        (
            UserID        INTEGER PRIMARY KEY AUTOINCREMENT,
            Name          TEXT    NOT NULL,
            Age           INTEGER NOT NULL,
            PhNum         TEXT    NOT NULL,
            SecurityLevel INTEGER NOT NULL,
            PasswordHash  TEXT    NOT NULL,
            IsActive      INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    print("Employee table created.")

    cur.execute(
        """
        CREATE TABLE EmpPayRaise
        (
            PayRaiseID   INTEGER PRIMARY KEY AUTOINCREMENT,
            EmpID        INTEGER NOT NULL,
            PayRaiseDate TEXT    NOT NULL,
            RaiseAmt     TEXT    NOT NULL,
            FOREIGN KEY (EmpID) REFERENCES Employee (UserID)
        )
        """
    )
    print("EmpPayRaise table created.")

    cur.execute(
        """
        CREATE TABLE AuditLog
        (
            AuditLogID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID     INTEGER,
            Action     TEXT NOT NULL,
            Details    TEXT,
            CreatedAt  TEXT NOT NULL
        )
        """
    )
    print("AuditLog table created.")

    employees = [
        ("PDiana", 34, "8135550001", 1, "test123"),
        ("TJones", 68, "8135550002", 2, "test123"),
        ("AMath", 29, "8135550003", 3, "test123"),
        ("BSmith", 37, "8135550004", 2, "test123"),
        ("CJones", 41, "8135550005", 3, "test123"),
        ("KLee", 25, "8135550006", 1, "test123"),
    ]

    for name, age, ph, level, pwd in employees:
        cur.execute(
            """
            INSERT INTO Employee (Name, Age, PhNum, SecurityLevel, PasswordHash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (enc(name), age, enc(ph), level, generate_password_hash(pwd)),
        )

    raises = [
        (1, "2020-01-11", 213.77),
        (2, "2022-04-17", 37.33),
        (3, "2024-09-21", 1324.98),
        (1, "2025-01-31", 67.99),
        (4, "2025-03-15", 150.00),
        (2, "2025-06-01", 89.50),
    ]

    for emp_id, dt, amt in raises:
        cur.execute(
            """
            INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
            VALUES (?, ?, ?)
            """,
            (emp_id, dt, enc(str(amt))),
        )

    conn.commit()

    print()
    print("Demo credentials for local testing:")
    print("UserID | Name       | SecurityLevel | Password")
    for row in cur.execute(
            "SELECT UserID, Name, SecurityLevel FROM Employee"
    ):
        user_id = row[0]
        name = dec(row[1])
        level = row[2]
        print(f"{user_id:6} | {name:10} | {level:13} | test123")

    conn.close()
    print("Connection closed.")


if __name__ == "__main__":
    reset_demo_database()
