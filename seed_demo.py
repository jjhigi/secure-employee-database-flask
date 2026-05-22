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


def seed_demo_data() -> None:
    """Insert demo employee and pay raise records if the database is empty."""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM Employee")
        employee_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM EmpPayRaise")
        pay_raise_count = cur.fetchone()[0]

        if employee_count > 0 or pay_raise_count > 0:
            print("Demo data was not inserted because the database already has records.")
            print(
                "Use reset_demo_db.py if you intentionally want to rebuild "
                "the demo database."
            )
            return

        employees = [
            ("PDiana", 34, "8135550001", 1),
            ("TJones", 68, "8135550002", 2),
            ("AMath", 29, "8135550003", 3),
            ("BSmith", 37, "8135550004", 2),
            ("CJones", 41, "8135550005", 3),
            ("KLee", 25, "8135550006", 1),
        ]

        for name, age, phone, security_level in employees:
            cur.execute(
                """
                INSERT INTO Employee (Name, Age, PhNum, SecurityLevel, PasswordHash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    enc(name),
                    age,
                    enc(phone),
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

        print("Demo data inserted successfully.")
        print()
        print("Demo credentials for local testing:")
        print("UserID | Name       | Role         | Password")

        for row in cur.execute("SELECT UserID, Name, SecurityLevel FROM Employee"):
            user_id = row[0]
            name = dec(row[1])
            security_level = row[2]
            role = SECURITY_LEVEL_LABELS.get(security_level, "Unknown")

            print(f"{user_id:6} | {name:10} | {role:12} | {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed_demo_data()
