"""
Demo Data Seed Script

Adds sample employee and pay raise records to the local SQLite database for
testing Flask Employee Manager.

This script assumes the database tables already exist. Run init_db.py first.
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


def seed_demo_data():
    """Insert demo employee and pay raise records if the database is empty."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Employee")
    employee_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM EmpPayRaise")
    pay_raise_count = cur.fetchone()[0]

    if employee_count > 0 or pay_raise_count > 0:
        print("Demo data was not inserted because the database already contains records.")
        print("Use reset_demo_db.py if you intentionally want to rebuild the demo database.")
        conn.close()
        return

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

    print("Demo data inserted successfully.")
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


if __name__ == "__main__":
    seed_demo_data()
