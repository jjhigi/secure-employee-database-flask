"""
Authentication and Setup Routes

Contains routes for first-admin setup, login, logout, home, session validation,
and changing the logged-in user's password.
"""

import sqlite3 as sql

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from audit import log_audit
from crypto_helpers import dec, enc
from db import get_db
from validation_constants import (
    MAX_NAME_LENGTH,
    MAX_PASSWORD_LENGTH,
    MAX_PHONE_LENGTH,
    MIN_PASSWORD_LENGTH,
)

auth_bp = Blueprint("auth", __name__)


# --------------------------
# Session / Account Helpers
# --------------------------
def employee_count():
    """Return the number of employee records in the database."""
    with get_db() as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM Employee")
        return cur.fetchone()[0]


def require_login():
    """
    Require a valid logged-in session.

    The session is checked against the current database record so inactive
    accounts, deleted accounts, and stale password-hash sessions are cleared.
    """
    if "UserID" not in session:
        return render_template("login.html")

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            """
            SELECT UserID, Name, SecurityLevel, PasswordHash, IsActive
            FROM Employee
            WHERE UserID = ?
            """,
            (session["UserID"],),
        )
        row = cur.fetchone()

    if not row or row["IsActive"] != 1:
        session.clear()
        flash("Your session is no longer valid. Please log in again.")
        return redirect(url_for("auth.login"))

    if session.get("PasswordHash") != row["PasswordHash"]:
        session.clear()
        flash("Your session is no longer valid. Please log in again.")
        return redirect(url_for("auth.login"))

    session["name"] = dec(row["Name"])
    session["SecurityLevel"] = int(row["SecurityLevel"])

    return None


# --------------------------
# Home
# --------------------------
@auth_bp.route("/")
def home():
    """Show the home page or redirect to first-admin setup when the database is empty."""
    if employee_count() == 0:
        session.clear()
        return redirect(url_for("auth.setup_admin"))

    guard = require_login()
    if guard:
        return guard

    return render_template("home.html", name=session.get("name"))


# --------------------------
# First Admin Setup
# --------------------------
@auth_bp.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():
    """Create the first admin account when the Employee table is empty."""
    if employee_count() > 0:
        return render_template(
            "result.html",
            msg="Initial admin setup is already complete.",
        )

    session.clear()

    if request.method == "POST":
        name = request.form.get("Name", "").strip()
        age = request.form.get("Age", "").strip()
        phone = request.form.get("PhNum", "").strip()
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
            errors.append(
                f"Phone number cannot be longer than {MAX_PHONE_LENGTH} characters."
            )

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

        with get_db() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO Employee
                    (Name, Age, PhNum, SecurityLevel, PasswordHash, IsActive)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    enc(name),
                    int(age),
                    enc(phone),
                    1,
                    generate_password_hash(password),
                    1,
                ),
            )
            con.commit()

        flash("Initial admin account created. Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("setup_admin.html")


# --------------------------
# Login / Logout
# --------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Log in an active employee by matching the decrypted name and password hash.

    Employee names are encrypted at rest, so login checks each decrypted name
    until it finds a matching username.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        matching_user = None

        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM Employee")
            rows = cur.fetchall()

        for row in rows:
            try:
                decrypted_name = dec(row["Name"])
            except Exception:
                continue

            if decrypted_name == username:
                matching_user = row
                break

        if (
                matching_user
                and matching_user["IsActive"] == 1
                and check_password_hash(matching_user["PasswordHash"], password)
        ):
            session.clear()
            session["UserID"] = matching_user["UserID"]
            session["name"] = dec(matching_user["Name"])
            session["SecurityLevel"] = int(matching_user["SecurityLevel"])
            session["PasswordHash"] = matching_user["PasswordHash"]

            flash("Login successful.")
            return redirect(url_for("auth.home"))

        session.clear()
        flash("Invalid username and/or password!")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Log out the current user by clearing the session."""
    session.clear()
    return redirect(url_for("auth.login"))


# --------------------------
# Change Own Password
# --------------------------
@auth_bp.route("/changepassword", methods=["GET", "POST"])
def changepassword():
    """Allow the logged-in user to change their own password."""
    guard = require_login()
    if guard:
        return guard

    user_id = session["UserID"]

    if request.method == "POST":
        current_password = request.form.get("CurrentPassword", "").strip()
        new_password = request.form.get("NewPassword", "").strip()
        confirm_password = request.form.get("ConfirmPassword", "").strip()

        errors = []

        if not current_password:
            errors.append("Current password cannot be empty.")

        if not new_password:
            errors.append("New password cannot be empty.")
        elif len(new_password) < MIN_PASSWORD_LENGTH:
            errors.append(
                f"New password must be at least {MIN_PASSWORD_LENGTH} characters."
            )
        elif len(new_password) > MAX_PASSWORD_LENGTH:
            errors.append(
                f"New password cannot be longer than {MAX_PASSWORD_LENGTH} characters."
            )

        if new_password != confirm_password:
            errors.append("New passwords do not match.")

        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                "SELECT PasswordHash FROM Employee WHERE UserID=?",
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            errors.append("User account was not found.")
        elif current_password and not check_password_hash(
                row["PasswordHash"],
                current_password,
        ):
            errors.append("Current password is incorrect.")

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        new_password_hash = generate_password_hash(new_password)

        with get_db() as con:
            cur = con.cursor()
            cur.execute(
                """
                UPDATE Employee
                SET PasswordHash=?
                WHERE UserID = ?
                """,
                (new_password_hash, user_id),
            )
            con.commit()

        session["PasswordHash"] = new_password_hash
        log_audit("CHANGE_PASSWORD", "User changed their own password.")

        flash("Password changed successfully.")
        return redirect(url_for("auth.home"))

    return render_template("changepassword.html")
