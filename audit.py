"""
Audit Logging Helper

Provides a shared helper for writing selected sensitive actions to the local
AuditLog table.
"""

from datetime import datetime

from flask import session

from db import get_db


def log_audit(action: str, details: str = "") -> None:
    """Write an audit log entry for the current session user."""
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
