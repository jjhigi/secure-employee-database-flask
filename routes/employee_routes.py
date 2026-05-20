"""
Employee and Admin Routes

Contains routes for employee management, password resets, account activation,
and viewing the audit log.
"""

import sqlite3 as sql

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash

from audit import log_audit
from db import get_db
from routes.auth_routes import dec, enc, require_login

employee_bp = Blueprint("employee", __name__)

# --------------------------
# Validation Constants
# --------------------------
MAX_NAME_LENGTH = 50
MAX_PHONE_LENGTH = 20
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


# --------------------------
# Access Control
# --------------------------
def require_level(allowed):
    """Require that the current user has one of the allowed security levels."""
    guard = require_login()
    if guard:
        return guard

    if session.get("SecurityLevel") not in allowed:
        return abort(404)

    return None


# --------------------------
# Add Employee (Admin only)
# --------------------------
@employee_bp.route("/addemployee")
def addemployee():
    guard = require_level({1})
    if guard:
        return guard

    return render_template("addemployee.html")


@employee_bp.route("/addrec", methods=["POST"])
def addrec():
    """Insert a new employee with encrypted fields and a hashed password."""
    guard = require_level({1})
    if guard:
        return guard

    name = request.form.get("Name", "").strip()
    age = request.form.get("Age", "").strip()
    phone = request.form.get("PhNum", "").strip()
    security_level = request.form.get("SecurityLevel", "").strip()
    password = request.form.get("Password", "").strip()

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
        errors.append("Security level must be 1-3.")

    if not password:
        errors.append("Password cannot be empty.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters.")

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
# List Employees (Level 1 or 2)
# --------------------------
@employee_bp.route("/listemployees")
def listemployees():
    """List employees, with optional search by name, user ID, security level, or status."""
    guard = require_level({1, 2})
    if guard:
        return guard

    search = request.args.get("search", "").strip()

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
            "IsActive": r["IsActive"],
            "Status": "Active" if r["IsActive"] == 1 else "Inactive",
        }

        if search:
            search_lower = search.lower()

            matches_name = search_lower in employee["Name"].lower()
            matches_user_id = search_lower in str(employee["UserID"]).lower()
            matches_security_level = (
                    search_lower in str(employee["SecurityLevel"]).lower()
            )
            matches_status = search_lower in employee["Status"].lower()

            if (
                    matches_name
                    or matches_user_id
                    or matches_security_level
                    or matches_status
            ):
                decrypted.append(employee)
        else:
            decrypted.append(employee)

    return render_template("listemployees.html", rows=decrypted, search=search)


# --------------------------
# Edit Employee (Admin only)
# --------------------------
@employee_bp.route("/editemployee/<int:user_id>", methods=["GET", "POST"])
def editemployee(user_id):
    """Edit an existing employee record. Admin only."""
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
                errors.append("Security level must be 1-3.")

            if errors:
                return render_template("result.html", msg=", ".join(errors))

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
                    int(security_level),
                    user_id,
                ),
            )
            con.commit()

            return redirect(url_for("employee.listemployees"))

    employee = {
        "UserID": row["UserID"],
        "Name": dec(row["Name"]),
        "Age": row["Age"],
        "PhNum": dec(row["PhNum"]),
        "SecurityLevel": row["SecurityLevel"],
    }

    return render_template("editemployee.html", employee=employee)


# --------------------------
# Reset Employee Password (Admin only)
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
# Deactivate Employee (Admin only)
# --------------------------
@employee_bp.route("/deactivateemployee/<int:user_id>", methods=["POST"])
def deactivateemployee(user_id):
    """Mark an employee as inactive. Admin only."""
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
# Reactivate Employee (Admin only)
# --------------------------
@employee_bp.route("/reactivateemployee/<int:user_id>", methods=["POST"])
def reactivateemployee(user_id):
    """Mark an employee as active again. Admin only."""
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
# Audit Log Viewer (Admin only)
# --------------------------
@employee_bp.route("/auditlog")
def auditlog():
    """Show recent audit log entries. Admin only."""
    guard = require_level({1})
    if guard:
        return guard

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            """
            SELECT AuditLogID, UserID, Action, Details, CreatedAt
            FROM AuditLog
            ORDER BY CreatedAt DESC, AuditLogID DESC
                LIMIT 100
            """
        )
        rows = cur.fetchall()

    return render_template("auditlog.html", rows=rows)
