"""
Audit Logging Helper

Provides a shared helper for writing selected sensitive actions to the local
AuditLog table.
"""

from datetime import datetime

from flask import session

from db import get_db


def log_audit(action: str, details: str = ""):
    """Write a sensitive action to the local audit log."""
    user_id = session.get("UserID")

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO AuditLog (UserID, Action, Details, CreatedAt)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                action,
                details,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        con.commit()