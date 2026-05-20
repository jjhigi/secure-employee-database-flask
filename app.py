"""
Flask Employee Manager

Main Flask application for managing employee records and pay raise data.
Handles login, role-based access control, encrypted database fields,
CSRF protection, and socket-based pay raise operations.
"""

# Standard library imports
import hashlib
import hmac
import socket
import sqlite3 as sql
from datetime import datetime

# Flask/third-party imports
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

# Local imports
import Encryption
from audit import log_audit
from config import FLASK_DEBUG, FLASK_SECRET_KEY, HMAC_SECRET
from db import get_db
from routes.auth_routes import auth_bp, dec, enc, require_login

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

csrf = CSRFProtect(app)

app.register_blueprint(auth_bp)

# --------------------------
# Socket / HMAC Constants
# --------------------------
HMAC_TAG_LEN = 64  # sha3_512 digests are 64 bytes
HMAC_SEPARATOR = "^%$"  # separator between fields in the message
HMAC_HOST = "localhost"
HMAC_PORT = 8888

# --------------------------
# Validation Constants
# --------------------------
MAX_NAME_LENGTH = 50
MAX_PHONE_LENGTH = 20
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_RAISE_AMOUNT = 1000000.00


# --------------------------
# Access Control
# --------------------------
def require_level(allowed):
    """Require that the current user has one of the allowed security levels."""
    guard = require_login()
    if guard:
        return guard

    if session.get("SecurityLevel") not in allowed:
        # If the level is not allowed, pretend the page does not exist.
        return abort(404)

    return None


# --------------------------
# Add Employee (Admin only)
# --------------------------
@app.route("/addemployee")
def addemployee():
    guard = require_level({1})
    if guard:
        return guard

    return render_template("addemployee.html")


@app.route("/addrec", methods=["POST"])
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
@app.route("/listemployees")
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
@app.route("/editemployee/<int:user_id>", methods=["GET", "POST"])
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
                errors.append(f"Phone number cannot be longer than {MAX_PHONE_LENGTH} characters.")

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

            return redirect(url_for("listemployees"))

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
@app.route("/resetpassword/<int:user_id>", methods=["GET", "POST"])
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
                errors.append(f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters.")

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
@app.route("/deactivateemployee/<int:user_id>", methods=["POST"])
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

    return redirect(url_for("listemployees"))


# --------------------------
# Reactivate Employee (Admin only)
# --------------------------
@app.route("/reactivateemployee/<int:user_id>", methods=["POST"])
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

    return redirect(url_for("listemployees"))


# --------------------------
# Audit Log Viewer (Admin only)
# --------------------------
@app.route("/auditlog")
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


# --------------------------
# List Pay Raises (Level 2)
# --------------------------
@app.route("/listpayraises")
def listpayraises():
    """List pay raises, with optional filtering by employee ID, date range, and minimum amount."""
    guard = require_level({2})
    if guard:
        return guard

    emp_id_filter = request.args.get("emp_id", "").strip()
    start_date_filter = request.args.get("start_date", "").strip()
    end_date_filter = request.args.get("end_date", "").strip()
    min_amount_filter = request.args.get("min_amount", "").strip()

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM EmpPayRaise")
        rows = cur.fetchall()

    decrypted = []

    for r in rows:
        raise_amount = float(dec(r["RaiseAmt"]))

        pay_raise = {
            "PayRaiseID": r["PayRaiseID"],
            "EmpID": r["EmpID"],
            "PayRaiseDate": r["PayRaiseDate"],
            "RaiseAmt": raise_amount,
        }

        include_record = True

        if emp_id_filter:
            include_record = include_record and str(pay_raise["EmpID"]) == emp_id_filter

        if start_date_filter:
            include_record = (
                    include_record and pay_raise["PayRaiseDate"] >= start_date_filter
            )

        if end_date_filter:
            include_record = (
                    include_record and pay_raise["PayRaiseDate"] <= end_date_filter
            )

        if min_amount_filter:
            try:
                min_amount = float(min_amount_filter)
                include_record = include_record and pay_raise["RaiseAmt"] >= min_amount
            except ValueError:
                include_record = False

        if include_record:
            decrypted.append(pay_raise)

    return render_template(
        "listpayraises.html",
        rows=decrypted,
        emp_id_filter=emp_id_filter,
        start_date_filter=start_date_filter,
        end_date_filter=end_date_filter,
        min_amount_filter=min_amount_filter,
    )


# --------------------------
# My Pay Raises (current user)
# --------------------------
@app.route("/mypayraises")
def mypayraises():
    """Show only the pay raises for the currently logged-in user."""
    guard = require_login()
    if guard:
        return guard

    uid = session["UserID"]

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            """
            SELECT PayRaiseDate, RaiseAmt
            FROM EmpPayRaise
            WHERE EmpID = ?
            ORDER BY PayRaiseDate DESC
            """,
            (uid,),
        )
        rows = cur.fetchall()

    decrypted = []

    for r in rows:
        decrypted.append(
            {
                "PayRaiseDate": r["PayRaiseDate"],
                "RaiseAmt": float(dec(r["RaiseAmt"])),
            }
        )

    return render_template("mypayraises.html", rows=decrypted)


# --------------------------
# Add Pay Raise (for current user)
# --------------------------
@app.route("/addpayraise", methods=["GET", "POST"])
def addpayraise():
    """Add a new pay raise for the currently logged-in user."""
    guard = require_login()
    if guard:
        return guard

    if request.method == "POST":
        date = request.form.get("PayRaiseDate", "").strip()
        amount = request.form.get("RaiseAmt", "").strip()

        errors = []

        if not date:
            errors.append("Date is required.")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid date format.")

        try:
            amount_value = float(amount)
            if amount_value <= 0:
                errors.append("Raise must be positive.")
            elif amount_value > MAX_RAISE_AMOUNT:
                errors.append(f"Raise cannot be more than ${MAX_RAISE_AMOUNT:,.2f}.")
        except ValueError:
            errors.append("Raise must be a number.")

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        with get_db() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
                VALUES (?, ?, ?)
                """,
                (session["UserID"], date, enc(str(amount_value))),
            )
            con.commit()

        return render_template("result.html", msg="Pay raise added!")

    return render_template("addpayraise.html")


# --------------------------
# Submit to Delete a Pay Raise (Level 1 or 2)
# --------------------------
@app.route("/submitdeletepayraise", methods=["GET", "POST"])
def submitdeletepayraise():
    """
    Submit a request to delete a pay raise.

    Validates that the EmpID and PayRaiseDate exist in the EmpPayRaise table.
    If valid, sends an encrypted message to the local pay raise deletion server.
    """
    guard = require_level({1, 2})
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        date = request.form.get("PayRaiseDate", "").strip()

        errors = []

        if not emp_id:
            errors.append("EmpID is required.")
        elif not emp_id.isdigit():
            errors.append("EmpID must be a number.")

        if not date:
            errors.append("PayRaiseDate is required.")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                errors.append("PayRaiseDate must be YYYY-MM-DD.")

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM EmpPayRaise WHERE EmpID=? AND PayRaiseDate=?",
                (int(emp_id), date),
            )
            row = cur.fetchone()

        if not row:
            return render_template(
                "result.html",
                msg="No pay raise found for that EmpID and PayRaiseDate.",
            )

        plain_msg = f"{emp_id}{HMAC_SEPARATOR}{date}"
        encrypted_text = enc(plain_msg)

        host, port = "localhost", 9999

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.sendall(encrypted_text.encode("utf-8"))
            sock.close()

            return render_template(
                "result.html",
                msg="Test result successfully sent",
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - Test result NOT sent",
            )

    return render_template("submitdeletepayraise.html")


# --------------------------
# Send Authenticated Add Pay Raise Message (HMAC + Encryption)
# --------------------------
@app.route("/sendaddpayraisehmac", methods=["GET", "POST"])
def sendaddpayraisehmac():
    """
    Send an authenticated encrypted message to add a pay raise.

    Validates EmpID, PayRaiseDate, and RaiseAmt. If valid, builds a separated
    plaintext message, encrypts it, signs the plaintext with HMAC-SHA3-512,
    and sends ciphertext + tag to the local add-pay-raise socket server.
    """
    guard = require_login()
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        payraise_date = request.form.get("PayRaiseDate", "").strip()
        raise_amt = request.form.get("RaiseAmt", "").strip()

        errors = []

        if not emp_id:
            errors.append("EmpID is required.")
        elif not emp_id.isdigit():
            errors.append("EmpID must be a numeric value.")
        elif int(emp_id) <= 0:
            errors.append("EmpID must be greater than 0.")
        else:
            with get_db() as con:
                con.row_factory = sql.Row
                cur = con.cursor()
                cur.execute(
                    "SELECT UserID FROM Employee WHERE UserID=?",
                    (int(emp_id),),
                )
                row = cur.fetchone()

            if not row:
                errors.append("EmpID does not exist in the Employee table.")

        if not payraise_date:
            errors.append("PayRaiseDate is required.")
        else:
            try:
                datetime.strptime(payraise_date, "%Y-%m-%d")
            except ValueError:
                errors.append("PayRaiseDate must be a valid date in YYYY-MM-DD format.")

        if not raise_amt:
            errors.append("RaiseAmt is required.")
        else:
            try:
                amount_value = float(raise_amt)
                if amount_value <= 0:
                    errors.append("RaiseAmt must be greater than 0.")
                elif amount_value > MAX_RAISE_AMOUNT:
                    errors.append(f"RaiseAmt cannot be more than ${MAX_RAISE_AMOUNT:,.2f}.")
            except ValueError:
                errors.append("RaiseAmt must be a numeric value.")

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        body_text = f"{emp_id}{HMAC_SEPARATOR}{payraise_date}{HMAC_SEPARATOR}{raise_amt}"
        body_bytes = body_text.encode("utf-8")

        body_encrypted = Encryption.cipher.encrypt(body_bytes)

        tag = hmac.new(
            HMAC_SECRET,
            body_bytes,
            digestmod=hashlib.sha3_512,
        ).digest()

        sent_message = body_encrypted + tag

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HMAC_HOST, HMAC_PORT))
            sock.sendall(sent_message)
            sock.close()

            return render_template(
                "result.html",
                msg="Message to create a pay raise successfully sent",
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - Message to create a pay raise NOT sent",
            )

    return render_template("sendaddpayraisehmac.html")


# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)
