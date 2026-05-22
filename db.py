"""
Database Helper

Provides a shared helper for opening connections to the local SQLite database.
"""

import sqlite3 as sql

DB_NAME = "EmployeeDB.db"


def get_db() -> sql.Connection:
    """Return a new SQLite connection to the local employee database."""
    return sql.connect(DB_NAME)
