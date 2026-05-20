"""
Database Helper

Provides a shared helper for opening connections to the local SQLite database.
"""

import sqlite3 as sql

DB_NAME = "EmployeeDB.db"


def get_db():
    """Open a new connection to the EmployeeDB database."""
    return sql.connect(DB_NAME)