"""
Database Setup Script

Creates and seeds the SQLite database used by Flask Employee Manager.
The script rebuilds the Employee and EmpPayRaise tables and inserts
sample encrypted employee and pay raise records for testing.
"""

import sqlite3
import Encryption
from werkzeug.security import generate_password_hash

# --------------------------
# Helper encryption functions
# --------------------------
def enc(s: str) -> str:
    """Encrypt a Python string and return text for storage."""
    return Encryption.cipher.encrypt(s.encode("utf-8")).decode("utf-8")

def dec(s: str) -> str:
    """Decrypt text from SQLite back into a normal Python string."""
    return Encryption.cipher.decrypt(s)

# --------------------------
# Open database connection
# --------------------------
conn = sqlite3.connect("EmployeeDB.db")
cur = conn.cursor()

# --------------------------
# Drop tables if they exist
# --------------------------
try:
    cur.execute("DROP TABLE IF EXISTS EmpPayRaise")
    cur.execute("DROP TABLE IF EXISTS Employee")
    conn.commit()
    print("EmpPayRaise table dropped.")
    print("Employee table dropped.")
except Exception:
    # If the tables don't exist, let the script continue
    print("Tables did not exist.")

# --------------------------
# Create Employee table
# UserID, Name, Age, PhNum, SecurityLevel, PasswordHash
# Name and PhNum are stored as encrypted text.
# PasswordHash stores a one-way password hash.
# --------------------------
cur.execute(
    """
    CREATE TABLE Employee(
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name   TEXT NOT NULL,
        Age    INTEGER NOT NULL,
        PhNum  TEXT NOT NULL,
        SecurityLevel INTEGER NOT NULL,
        PasswordHash TEXT NOT NULL
    )
    """
)
print("Employee Table created.")

# --------------------------
# Create EmpPayRaise table
# PayRaiseID, EmpID, PayRaiseDate, RaiseAmt
# RaiseAmt is stored as encrypted text
# EmpID must match a valid UserID in Employee
# --------------------------
cur.execute(
    """
    CREATE TABLE EmpPayRaise(
        PayRaiseID INTEGER PRIMARY KEY AUTOINCREMENT,
        EmpID INTEGER NOT NULL,
        PayRaiseDate TEXT NOT NULL,
        RaiseAmt TEXT NOT NULL,
        FOREIGN KEY (EmpID) REFERENCES Employee(UserID)
    )
    """
)
print("EmpPayRaise Table created.")

# --------------------------
# Insert employees (with encrypted fields)
# --------------------------
employees = [
    ("PDiana", 34, "8135550001", 1, "test123"),
    ("TJones", 68, "8135550002", 2, "test123"),
    ("AMath", 29, "8135550003", 3, "test123"),
    ("BSmith", 37, "8135550004", 2, "test123"),
    ("CJones", 41, "8135550005", 3, "test123"),
    ("KLee",   25, "8135550006", 1, "test123"),
]

for name, age, ph, level, pwd in employees:
    cur.execute(
        """
        INSERT INTO Employee (Name, Age, PhNum, SecurityLevel, PasswordHash)
        VALUES (?, ?, ?, ?, ?)
        """,
        (enc(name), age, enc(ph), level, generate_password_hash(pwd)),
    )

# --------------------------
# Insert pay raises (RaiseAmt encrypted)
# --------------------------
raises = [
    (1, "2020-01-11", 213.77),
    (2, "2022-04-17", 37.33),
    (3, "2024-09-21", 1324.98),
    (1, "2025-01-31", 67.99),
    (4, "2025-03-15", 150.00),
    (2, "2025-06-01", 89.50),
]

for emp_id, dt, amt in raises:
    # Convert number to string before encrypting
    cur.execute(
        """
        INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
        VALUES (?, ?, ?)
        """,
        (emp_id, dt, enc(str(amt))),
    )

conn.commit()

# --------------------------
# Show all rows (encrypted values)
# --------------------------
print()
print("Employee table (encrypted values):")
for row in cur.execute("SELECT * FROM Employee"):
    print(row)

print()
print("EmpPayRaise table (encrypted RaiseAmt):")
for row in cur.execute("SELECT * FROM EmpPayRaise"):
    print(row)

# --------------------------
# Demo Login Credentials
# --------------------------
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
