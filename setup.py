"""
Setup Compatibility Script

Runs reset_demo_db.py to reset and rebuild the local demo database.

Warning: This script deletes existing Employee, EmpPayRaise, and AuditLog data.
For safe setup that does not delete records, use:
    python init_db.py

To add demo data after safe initialization, use:
    python seed_demo.py
"""

import reset_demo_db


def main() -> None:
    """Run the backward-compatible demo database reset command."""
    print("Warning: setup.py resets the demo database and deletes existing records.")
    print("For safe setup without deleting records, run init_db.py instead.")
    print()

    reset_demo_db.reset_demo_database()


if __name__ == "__main__":
    main()
