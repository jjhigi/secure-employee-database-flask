"""
Setup Compatibility Script

This script resets and rebuilds the demo database by running reset_demo_db.py.

For safer setup that does not delete existing data, use:
    python init_db.py

To add demo data after initialization, use:
    python seed_demo.py
"""

import reset_demo_db

if __name__ == "__main__":
    print("Warning: setup.py resets the demo database and deletes existing records.")
    print("For safer setup, run init_db.py instead.")
    print()
    reset_demo_db.reset_demo_database()
