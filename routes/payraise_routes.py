"""
Pay Raise Routes

Contains routes for viewing, adding, filtering, and socket-submitting pay raise
records.
"""

import hashlib
import hmac
import socket
import sqlite3 as sql
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    render_template,
    request,
    session,
)
from config import HMAC_SECRET
from db import get_db
from routes.auth_routes import dec, enc, require_login
import Encryption

payraise_bp = Blueprint("payraise", __name__)


# --------------------------
# Socket / HMAC Constants
# --------------------------
HMAC_TAG_LEN = 64
HMAC_SEPARATOR = "^%$"
HMAC_HOST = "localhost"
HMAC_PORT = 8888


# --------------------------
# Validation Constants
# --------------------------
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
        return abort(404)

    return None


# --------------------------
# List Pay Raises (Level 2)
# --------------------------
@payraise_bp.route("/listpayraises")
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
@payraise_bp.route("/mypayraises")
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
@payraise_bp.route("/addpayraise", methods=["GET", "POST"])
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
@payraise_bp.route("/submitdeletepayraise", methods=["GET", "POST"])
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
@payraise_bp.route("/sendaddpayraisehmac", methods=["GET", "POST"])
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
                    errors.append(
                        f"RaiseAmt cannot be more than ${MAX_RAISE_AMOUNT:,.2f}."
                    )
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