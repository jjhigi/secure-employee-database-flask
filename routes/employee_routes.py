"""
Employee and Admin Routes

Contains routes for employee management, password resets, account status changes,
and audit log viewing/filtering.
"""

from datetime import datetime
from pathlib import Path
import sqlite3 as sql

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash

from audit import log_audit
from auth_helpers import require_level
from crypto_helpers import dec, enc
from db import get_db
from validation_constants import (
    MAX_NAME_LENGTH,
    MAX_PASSWORD_LENGTH,
    MAX_PHONE_LENGTH,
    MIN_PASSWORD_LENGTH,
)

employee_bp = Blueprint("employee", __name__)

# --------------------------
# Security Level Labels
# --------------------------
SECURITY_LEVEL_LABELS = {
    1: "Admin",
    2: "Manager",
    3: "Employee",
}

SECURITY_LEVEL_OPTIONS = [
    {"value": 1, "label": "1 - Admin"},
    {"value": 2, "label": "2 - Manager"},
    {"value": 3, "label": "3 - Employee"},
]


def get_security_level_label(security_level):
    """Return a readable label for a numeric security level."""
    return SECURITY_LEVEL_LABELS.get(security_level, "Unknown")


# --------------------------
# Admin Dashboard
# --------------------------
@employee_bp.route("/dashboard")
def dashboard():
    """Show simple admin account totals."""
    guard = require_level({1})
    if guard:
        return guard

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM Employee")
        total_employees = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Employee WHERE IsActive = 1")
        active_employees = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Employee WHERE IsActive = 0")
        inactive_employees = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Employee WHERE SecurityLevel = 1")
        admin_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Employee WHERE SecurityLevel = 2")
        manager_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM Employee WHERE SecurityLevel = 3")
        employee_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM EmpPayRaise")
        total_pay_raises = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM EmpPayRaise WHERE IsVoided = 0")
        active_pay_raises = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM EmpPayRaise WHERE IsVoided = 1")
        voided_pay_raises = cur.fetchone()[0]

        cur.execute(
            """
            SELECT AuditLogID, UserID, Action, Details, CreatedAt
            FROM AuditLog
            ORDER BY CreatedAt DESC, AuditLogID DESC
            LIMIT 5
            """
        )
        audit_rows = cur.fetchall()

    recent_audit_entries = []

    for row in audit_rows:
        recent_audit_entries.append(
            {
                "CreatedAt": row["CreatedAt"],
                "UserID": row["UserID"],
                "Action": row["Action"],
                "Details": row["Details"],
            }
        )

    latest_backup_name = None
    latest_backup_timestamp = None
    backup_count = 0

    backup_dir = Path("backups")

    if backup_dir.exists():
        for backup_file in backup_dir.glob("EmployeeDB*.db"):
            backup_count += 1
            timestamp_text = "_".join(backup_file.stem.split("_")[-2:])

            try:
                backup_timestamp = datetime.strptime(
                    timestamp_text,
                    "%Y-%m-%d_%H-%M-%S",
                )
            except ValueError:
                continue

            if latest_backup_timestamp is None:
                latest_backup_name = backup_file.name
                latest_backup_timestamp = backup_timestamp
            elif backup_timestamp > latest_backup_timestamp:
                latest_backup_name = backup_file.name
                latest_backup_timestamp = backup_timestamp

    if latest_backup_timestamp is not None:
        latest_backup_timestamp = latest_backup_timestamp.strftime("%Y-%m-%d %H:%M:%S")

    stats = {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "admin_count": admin_count,
        "manager_count": manager_count,
        "employee_count": employee_count,
        "total_pay_raises": total_pay_raises,
        "active_pay_raises": active_pay_raises,
        "voided_pay_raises": voided_pay_raises,
        "backup_count": backup_count,
        "latest_backup_name": latest_backup_name,
        "latest_backup_timestamp": latest_backup_timestamp,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_audit_entries=recent_audit_entries,
    )


# --------------------------
# Add Employee
# --------------------------
@employee_bp.route("/addemployee")
def addemployee():
    """Show the add employee form. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    return render_template(
        "addemployee.html",
        security_level_options=SECURITY_LEVEL_OPTIONS,
    )


@employee_bp.route("/addrec", methods=["POST"])
def addrec():
    """Create an employee with encrypted fields and a hashed password. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    name = request.form.get("Name", "").strip()
    age = request.form.get("Age", "").strip()
    phone = request.form.get("PhNum", "").strip()
    security_level = request.form.get("SecurityLevel", "").strip()
    password = request.form.get("Password", "").strip()
    confirm_password = request.form.get("ConfirmPassword", "").strip()

    errors = []

    if not name:
        errors.append("Name cannot be empty.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Name cannot be longer than {MAX_NAME_LENGTH} characters.")

    if not age.isdigit() or not (1 <= int(age) <= 120):
        errors.append("Age must be 1-120.")

    if not phone:
        errors.append("Phone number cannot be empty.")
    elif len(phone) > MAX_PHONE_LENGTH:
        errors.append(f"Phone number cannot be longer than {MAX_PHONE_LENGTH} characters.")

    if not security_level.isdigit() or not (1 <= int(security_level) <= 3):
        errors.append("Security level must be 1 (Admin), 2 (Manager), or 3 (Employee).")

    if not password:
        errors.append("Password cannot be empty.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    if errors:
        return render_template("result.html", msg=", ".join(errors))

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO Employee (Name, Age, PhNum, SecurityLevel, PasswordHash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                enc(name),
                int(age),
                enc(phone),
                int(security_level),
                generate_password_hash(password),
            ),
        )
        con.commit()

    return render_template("result.html", msg="Employee added!")


# --------------------------
# List Employees
# --------------------------
@employee_bp.route("/listemployees")
def listemployees():
    """List employees with optional search. Level 1 or 2 only."""
    guard = require_level({1, 2})
    if guard:
        return guard

    search = request.args.get("search", "").strip()
    search_lower = search.lower()

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM Employee")
        rows = cur.fetchall()

    decrypted = []

    for r in rows:
        employee = {
            "UserID": r["UserID"],
            "Name": dec(r["Name"]),
            "Age": r["Age"],
            "PhNum": dec(r["PhNum"]),
            "SecurityLevel": r["SecurityLevel"],
            "SecurityLevelLabel": get_security_level_label(r["SecurityLevel"]),
            "IsActive": r["IsActive"],
            "Status": "Active" if r["IsActive"] == 1 else "Inactive",
        }

        if not search:
            decrypted.append(employee)
            continue

        matches_name = search_lower in employee["Name"].lower()
        matches_user_id = search_lower in str(employee["UserID"]).lower()
        matches_security_level = (
                search_lower in str(employee["SecurityLevel"]).lower()
                or search_lower in employee["SecurityLevelLabel"].lower()
        )
        matches_status = search_lower in employee["Status"].lower()

        if (
                matches_name
                or matches_user_id
                or matches_security_level
                or matches_status
        ):
            decrypted.append(employee)

    return render_template("listemployees.html", rows=decrypted, search=search)


# --------------------------
# Edit Employee
# --------------------------
@employee_bp.route("/editemployee/<int:user_id>", methods=["GET", "POST"])
def editemployee(user_id):
    """Edit an employee record. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute(
            "SELECT * FROM Employee WHERE UserID=?",
            (user_id,),
        )
        row = cur.fetchone()

        if not row:
            return render_template("result.html", msg="Employee not found.")

        if request.method == "POST":
            name = request.form.get("Name", "").strip()
            age = request.form.get("Age", "").strip()
            phone = request.form.get("PhNum", "").strip()
            security_level = request.form.get("SecurityLevel", "").strip()

            errors = []

            if not name:
                errors.append("Name cannot be empty.")
            elif len(name) > MAX_NAME_LENGTH:
                errors.append(f"Name cannot be longer than {MAX_NAME_LENGTH} characters.")

            if not age.isdigit() or not (1 <= int(age) <= 120):
                errors.append("Age must be 1-120.")

            if not phone:
                errors.append("Phone number cannot be empty.")
            elif len(phone) > MAX_PHONE_LENGTH:
                errors.append(
                    f"Phone number cannot be longer than {MAX_PHONE_LENGTH} characters."
                )

            if not security_level.isdigit() or not (1 <= int(security_level) <= 3):
                errors.append(
                    "Security level must be 1 (Admin), 2 (Manager), or 3 (Employee)."
                )

            if errors:
                return render_template("result.html", msg=", ".join(errors))

            old_security_level = row["SecurityLevel"]
            new_security_level = int(security_level)

            cur.execute(
                """
                UPDATE Employee
                SET Name=?,
                    Age=?,
                    PhNum=?,
                    SecurityLevel=?
                WHERE UserID = ?
                """,
                (
                    enc(name),
                    int(age),
                    enc(phone),
                    new_security_level,
                    user_id,
                ),
            )
            con.commit()

            if old_security_level != new_security_level:
                old_label = get_security_level_label(old_security_level)
                new_label = get_security_level_label(new_security_level)

                log_audit(
                    "CHANGE_SECURITY_LEVEL",
                    (
                        f"Changed UserID {user_id} security level from "
                        f"{old_label} ({old_security_level}) to "
                        f"{new_label} ({new_security_level})."
                    ),
                )

            return redirect(url_for("employee.listemployees"))

    employee = {
        "UserID": row["UserID"],
        "Name": dec(row["Name"]),
        "Age": row["Age"],
        "PhNum": dec(row["PhNum"]),
        "SecurityLevel": row["SecurityLevel"],
    }

    return render_template(
        "editemployee.html",
        employee=employee,
        security_level_options=SECURITY_LEVEL_OPTIONS,
    )


# --------------------------
# Reset Employee Password
# --------------------------
@employee_bp.route("/resetpassword/<int:user_id>", methods=["GET", "POST"])
def resetpassword(user_id):
    """Reset an employee password by storing a new password hash. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute(
            "SELECT UserID, Name FROM Employee WHERE UserID=?",
            (user_id,),
        )
        row = cur.fetchone()

        if not row:
            return render_template("result.html", msg="Employee not found.")

        employee = {
            "UserID": row["UserID"],
            "Name": dec(row["Name"]),
        }

        if request.method == "POST":
            password = request.form.get("Password", "").strip()
            confirm_password = request.form.get("ConfirmPassword", "").strip()

            errors = []

            if not password:
                errors.append("Password cannot be empty.")
            elif len(password) < MIN_PASSWORD_LENGTH:
                errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
            elif len(password) > MAX_PASSWORD_LENGTH:
                errors.append(
                    f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters."
                )

            if password != confirm_password:
                errors.append("Passwords do not match.")

            if errors:
                return render_template("result.html", msg=", ".join(errors))

            cur.execute(
                """
                UPDATE Employee
                SET PasswordHash=?
                WHERE UserID = ?
                """,
                (generate_password_hash(password), user_id),
            )
            con.commit()

            log_audit("RESET_PASSWORD", f"Reset password for UserID {user_id}.")

            return render_template("result.html", msg="Password reset successfully.")

    return render_template("resetpassword.html", employee=employee)


# --------------------------
# Deactivate Employee
# --------------------------
@employee_bp.route("/deactivateemployee/<int:user_id>", methods=["POST"])
def deactivateemployee(user_id):
    """Mark an employee account as inactive. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    if session.get("UserID") == user_id:
        return render_template("result.html", msg="You cannot deactivate your own account.")

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            "UPDATE Employee SET IsActive=0 WHERE UserID=?",
            (user_id,),
        )
        con.commit()

    log_audit("DEACTIVATE_EMPLOYEE", f"Deactivated UserID {user_id}.")

    return redirect(url_for("employee.listemployees"))


# --------------------------
# Reactivate Employee
# --------------------------
@employee_bp.route("/reactivateemployee/<int:user_id>", methods=["POST"])
def reactivateemployee(user_id):
    """Reactivate an inactive employee account. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            "UPDATE Employee SET IsActive=1 WHERE UserID=?",
            (user_id,),
        )
        con.commit()

    log_audit("REACTIVATE_EMPLOYEE", f"Reactivated UserID {user_id}.")

    return redirect(url_for("employee.listemployees"))


# --------------------------
# Audit Log
# --------------------------
@employee_bp.route("/auditlog")
def auditlog():
    """Show recent audit log entries with optional filters. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    action = request.args.get("action", "").strip()
    user_id = request.args.get("user_id", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    search = request.args.get("search", "").strip()

    filters = {
        "action": action,
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date,
        "search": search,
    }

    errors = []
    where_clauses = []
    params = []

    if action:
        where_clauses.append("Action = ?")
        params.append(action)

    if user_id:
        if user_id.isdigit():
            where_clauses.append("UserID = ?")
            params.append(int(user_id))
        else:
            errors.append("User ID must be a number.")

    if start_date:
        where_clauses.append("CreatedAt >= ?")
        params.append(start_date + " 00:00:00")

    if end_date:
        where_clauses.append("CreatedAt <= ?")
        params.append(end_date + " 23:59:59")

    if search:
        where_clauses.append("Details LIKE ?")
        params.append(f"%{search}%")

    query = """
            SELECT AuditLogID, UserID, Action, Details, CreatedAt
            FROM AuditLog \
            """

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += """
        ORDER BY CreatedAt DESC, AuditLogID DESC
        LIMIT 100
    """

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()

        cur.execute(
            """
            SELECT DISTINCT Action
            FROM AuditLog
            ORDER BY Action
            """
        )
        actions = cur.fetchall()

        if errors:
            rows = []
        else:
            cur.execute(query, params)
            rows = cur.fetchall()

    return render_template(
        "auditlog.html",
        rows=rows,
        actions=actions,
        filters=filters,
        errors=errors,
    )
