"""
Reset Demo Database Script

Deletes and recreates the local SQLite demo database, then inserts sample
employee and pay raise records for local testing.

Warning: This script removes existing Employee, EmpPayRaise, and AuditLog data.
Use init_db.py for safe database initialization without deleting records.
"""

import sqlite3

import Encryption
from werkzeug.security import generate_password_hash

DB_NAME = "EmployeeDB.db"
DEMO_PASSWORD = "test123"

SECURITY_LEVEL_LABELS = {
    1: "Admin",
    2: "Manager",
    3: "Employee",
}


def enc(value: str) -> str:
    """Encrypt a string for SQLite storage."""
    return Encryption.cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def dec(value: str) -> str:
    """Decrypt a stored SQLite value back into a string."""
    return Encryption.cipher.decrypt(value)


def reset_demo_database():
    """Rebuild the demo database and seed it with sample records."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS AuditLog")
    cur.execute("DROP TABLE IF EXISTS EmpPayRaise")
    cur.execute("DROP TABLE IF EXISTS Employee")
    conn.commit()

    print("AuditLog table dropped.")
    print("EmpPayRaise table dropped.")
    print("Employee table dropped.")

    cur.execute(
        """
        CREATE TABLE Employee
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
    print("Employee table created.")

    cur.execute(
        """
        CREATE TABLE EmpPayRaise
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
        ("PDiana", 34, "8135550001", 78250.00, 1),
        ("TJones", 68, "8135550002", 68950.00, 2),
        ("AMath", 29, "8135550003", 54800.00, 3),
        ("BSmith", 37, "8135550004", 72150.00, 2),
        ("CJones", 41, "8135550005", 59300.00, 3),
        ("KLee", 25, "8135550006", 76400.00, 1),
    ]

    for name, age, phone, current_salary, security_level in employees:
        cur.execute(
            """
            INSERT INTO Employee
                (Name, Age, PhNum, CurrentSalary, SecurityLevel, PasswordHash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                enc(name),
                age,
                enc(phone),
                enc(f"{current_salary:.2f}"),
                security_level,
                generate_password_hash(DEMO_PASSWORD),
            ),
        )

    pay_raises = [
        (1, "2020-01-11", 213.77),
        (2, "2022-04-17", 37.33),
        (3, "2024-09-21", 1324.98),
        (1, "2025-01-31", 67.99),
        (4, "2025-03-15", 150.00),
        (2, "2025-06-01", 89.50),
    ]

    for emp_id, pay_raise_date, amount in pay_raises:
        cur.execute(
            """
            INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
            VALUES (?, ?, ?)
            """,
            (emp_id, pay_raise_date, enc(str(amount))),
        )

    conn.commit()

    print()
    print("Demo credentials for local testing:")
    print("UserID | Name       | Role         | Password")

    for row in cur.execute("SELECT UserID, Name, SecurityLevel FROM Employee"):
        user_id = row[0]
        name = dec(row[1])
        security_level = row[2]
        role = SECURITY_LEVEL_LABELS.get(security_level, "Unknown")

        print(f"{user_id:6} | {name:10} | {role:12} | {DEMO_PASSWORD}")

    conn.close()
    print("Connection closed.")


if __name__ == "__main__":
    reset_demo_database()
