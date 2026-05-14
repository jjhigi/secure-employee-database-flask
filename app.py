"""
Flask Employee Manager

Main Flask application for managing employee records and pay raise data.
Handles login, role-based access control, encrypted database fields,
and socket-based pay raise operations.
"""

from flask import Flask, abort, render_template, request, redirect, url_for, session, flash
import sqlite3 as sql
from datetime import datetime
import Encryption
import socket
import hmac
import hashlib

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# --------------------------
# HMAC / socket constants
# --------------------------
HMAC_SECRET = b"1234"        # shared secret between client and server
HMAC_TAG_LEN = 64            # sha3_512 digests are 64 bytes
HMAC_SEPARATOR = "^%$"       # separator between fields in the message
HMAC_HOST = "localhost"
HMAC_PORT = 8888


# --------------------------
# Helpers
# --------------------------
def get_db():
    """Open a new connection to the EmployeeDB database."""
    return sql.connect("EmployeeDB.db")


def enc(s: str) -> str:
    """Encrypt a Python string and return text."""
    return Encryption.cipher.encrypt(s.encode("utf-8")).decode("utf-8")


def dec(s: str) -> str:
    """Decrypt text from the database back into a normal string."""
    return Encryption.cipher.decrypt(s)


# --------------------------
# Access Control
# --------------------------
def require_login():
    """If user is not logged in, send them to the login page."""
    if "UserID" not in session:
        return render_template("login.html")
    return None


def require_level(allowed):
    """Require that the current user has one of the allowed security levels."""
    guard = require_login()
    if guard:
        return guard
    if session.get("SecurityLevel") not in allowed:
        # If level is not allowed, pretend the page doesn't exist
        return abort(404)
    return None


# --------------------------
# Routes
# --------------------------
@app.route("/")
def home():
    guard = require_login()
    if guard:
        return guard
    return render_template("home.html", name=session.get("name"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in user by matching encrypted username and password."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        enc_name = enc(username)
        enc_pwd = enc(password)

        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM Employee WHERE Name=? AND LoginPassword=?",
                (enc_name, enc_pwd),
            )
            row = cur.fetchone()

        if row:
            # Store decrypted name and security level in the session
            session.clear()
            session["UserID"] = row["UserID"]
            session["name"] = dec(row["Name"])
            session["SecurityLevel"] = int(row["SecurityLevel"])
            flash("Login successful.")
            return redirect(url_for("home"))
        else:
            session.clear()
            flash("Invalid username and/or password!")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log out user by clearing the session."""
    session.clear()
    return redirect(url_for("login"))


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
    """Insert a new employee with encrypted fields."""
    guard = require_level({1})
    if guard:
        return guard

    nm = request.form.get("Name", "").strip()
    ag = request.form.get("Age", "").strip()
    ph = request.form.get("PhNum", "").strip()
    lvl = request.form.get("SecurityLevel", "").strip()
    pwd = request.form.get("LoginPassword", "").strip()

    errors = []
    if not nm:
        errors.append("Name cannot be empty.")
    if not ag.isdigit() or not (1 <= int(ag) <= 120):
        errors.append("Age must be 1-120.")
    if not ph:
        errors.append("Phone number cannot be empty.")
    if not lvl.isdigit() or not (1 <= int(lvl) <= 3):
        errors.append("SecurityLevel must be 1-3.")
    if not pwd:
        errors.append("Password cannot be empty.")

    if errors:
        # Show all validation messages on a simple result page
        return render_template("result.html", msg=", ".join(errors))

    with get_db() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO Employee (Name, Age, PhNum, SecurityLevel, LoginPassword)
            VALUES (?, ?, ?, ?, ?)
            """,
            (enc(nm), int(ag), enc(ph), int(lvl), enc(pwd)),
        )
        con.commit()

    return render_template("result.html", msg="Employee added!")


# --------------------------
# List Employees (Level 1 or 2)
# --------------------------
@app.route("/listemployees")
def listemployees():
    """List employees, with optional search by name, user ID, or security level."""
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
            "LoginPassword": dec(r["LoginPassword"]),
        }

        if search:
            search_lower = search.lower()

            matches_name = search_lower in employee["Name"].lower()
            matches_user_id = search_lower in str(employee["UserID"]).lower()
            matches_security_level = search_lower in str(employee["SecurityLevel"]).lower()

            if matches_name or matches_user_id or matches_security_level:
                decrypted.append(employee)
        else:
            decrypted.append(employee)

    return render_template("listemployees.html", rows=decrypted, search=search)


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
            include_record = include_record and pay_raise["PayRaiseDate"] >= start_date_filter

        if end_date_filter:
            include_record = include_record and pay_raise["PayRaiseDate"] <= end_date_filter

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
            "SELECT PayRaiseDate, RaiseAmt FROM EmpPayRaise WHERE EmpID=? ORDER BY PayRaiseDate DESC",
            (uid,),
        )
        rows = cur.fetchall()

    decrypted = []
    for r in rows:
        decrypted.append({
            "PayRaiseDate": r["PayRaiseDate"],
            "RaiseAmt": float(dec(r["RaiseAmt"])),
        })

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
        dt = request.form.get("PayRaiseDate", "").strip()
        amt = request.form.get("RaiseAmt", "").strip()

        errors = []
        if not dt:
            errors.append("Date is required.")
        else:
            try:
                datetime.strptime(dt, "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid date format.")

        try:
            val = float(amt)
            if val <= 0:
                errors.append("Raise must be positive.")
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
                (session["UserID"], dt, enc(str(val))),
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
    Page to submit a request to delete a pay raise.
    - Validates EmpID and PayRaiseDate exist in EmpPayRaise.
    - If valid, sends encrypted message via socket to localhost:9999.
    """
    guard = require_level({1, 2})
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        dt = request.form.get("PayRaiseDate", "").strip()

        # Basic validation
        errors = []
        if not emp_id:
            errors.append("EmpID is required.")
        elif not emp_id.isdigit():
            errors.append("EmpID must be a number.")

        if not dt:
            errors.append("PayRaiseDate is required.")
        else:
            try:
                datetime.strptime(dt, "%Y-%m-%d")
            except ValueError:
                errors.append("PayRaiseDate must be YYYY-MM-DD.")

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        # Check that a matching record exists
        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM EmpPayRaise WHERE EmpID=? AND PayRaiseDate=?",
                (int(emp_id), dt),
            )
            row = cur.fetchone()

        if not row:
            # Data validation issue: no matching row
            return render_template(
                "result.html",
                msg="No pay raise found for that EmpID and PayRaiseDate."
            )

        # Build message "EmpID^%$PayRaiseDate"
        separator = "^%$"
        plain_msg = f"{emp_id}{separator}{dt}"

        # Encrypt the message using the same cipher helper
        encrypted_text = enc(plain_msg)

        # Try to open a socket and send the encrypted message
        HOST, PORT = "localhost", 9999
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            sock.sendall(encrypted_text.encode("utf-8"))
            sock.close()
            return render_template(
                "result.html",
                msg="Test result successfully sent"
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - Test result NOT sent"
            )

    # GET -> show form
    return render_template("submitdeletepayraise.html")


# --------------------------
# Send Authenticated Add Pay Raise Message (HMAC + Encryption)
# --------------------------
@app.route("/sendaddpayraisehmac", methods=["GET", "POST"])
def sendaddpayraisehmac():
    """
    Page to send an authenticated (HMAC + Encryption) message to add a pay raise.
    - Validates EmpID > 0 and exists in Employee table.
    - Validates PayRaiseDate is a valid date.
    - Validates RaiseAmt is numeric and > 0.
    - If valid, builds a message with a separator, encrypts it with AES,
      computes an HMAC (sha3_512) over the plaintext message, concatenates
      ciphertext + tag, and sends to localhost:8888 via socket.
    - Shows a result page with success / failure message.
    """
    guard = require_login()  # available to all logged-in users
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        payraise_date = request.form.get("PayRaiseDate", "").strip()
        raise_amt = request.form.get("RaiseAmt", "").strip()

        errors = []

        # Validate EmpID is numeric and > 0
        if not emp_id:
            errors.append("EmpID is required.")
        else:
            if not emp_id.isdigit():
                errors.append("EmpID must be a numeric value.")
            else:
                if int(emp_id) <= 0:
                    errors.append("EmpID must be greater than 0.")
                else:
                    # Check EmpID exists in Employee table
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

        # Validate PayRaiseDate
        if not payraise_date:
            errors.append("PayRaiseDate is required.")
        else:
            try:
                datetime.strptime(payraise_date, "%Y-%m-%d")
            except ValueError:
                errors.append("PayRaiseDate must be a valid date in YYYY-MM-DD format.")

        # Validate RaiseAmt
        if not raise_amt:
            errors.append("RaiseAmt is required.")
        else:
            try:
                amt_val = float(raise_amt)
                if amt_val <= 0:
                    errors.append("RaiseAmt must be greater than 0.")
            except ValueError:
                errors.append("RaiseAmt must be a numeric value.")

        # If any validation failed, show the issues
        if errors:
            return render_template("result.html", msg=", ".join(errors))

        # All fields valid -> build the plaintext message with a separator
        body_text = f"{emp_id}{HMAC_SEPARATOR}{payraise_date}{HMAC_SEPARATOR}{raise_amt}"
        body_bytes = body_text.encode("utf-8")

        # Encrypt the message (AES CFB using Encryption.py)
        body_encrypted = Encryption.cipher.encrypt(body_bytes)  # returns base64 bytes

        # Compute HMAC tag over plaintext (like ExampleEncryptionHMAC.py)
        tag = hmac.new(
            HMAC_SECRET,
            body_bytes,
            digestmod=hashlib.sha3_512
        ).digest()

        # Final message is ciphertext + tag
        sent_message = body_encrypted + tag

        # Try to open connection and send
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HMAC_HOST, HMAC_PORT))
            sock.sendall(sent_message)
            sock.close()
            return render_template(
                "result.html",
                msg="Message to create a pay raise successfully sent"
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - Message to create a pay raise NOT sent"
            )

    # GET -> show the form
    return render_template("sendaddpayraisehmac.html")


# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
