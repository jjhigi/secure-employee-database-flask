"""
Pay Raise Routes

Contains routes for viewing, adding, filtering, voiding, and socket-submitting
pay raise records.
"""

import hashlib
import hmac
import socket
import sqlite3 as sql

from flask import (
    Blueprint,
    render_template,
    request,
    session,
)

import Encryption
from audit import log_audit
from auth_helpers import require_level
from config import HMAC_SECRET
from crypto_helpers import dec
from db import get_db
from routes.auth_routes import require_login
from validation_helpers import (
    validate_employee_id,
    validate_payraise_date,
    validate_raise_amount,
)

payraise_bp = Blueprint("payraise", __name__)

# --------------------------
# Socket / HMAC Constants
# --------------------------
HMAC_SEPARATOR = "^%$"
HMAC_HOST = "localhost"
HMAC_PORT = 8888

VOID_HOST = "localhost"
VOID_PORT = 9999


# --------------------------
# List Pay Raises
# --------------------------
@payraise_bp.route("/listpayraises")
def listpayraises():
    """List all pay raises with optional filters. Level 1 or 2 only."""
    guard = require_level({1, 2})
    if guard:
        return guard

    emp_id_filter = request.args.get("emp_id", "").strip()
    start_date_filter = request.args.get("start_date", "").strip()
    end_date_filter = request.args.get("end_date", "").strip()
    min_amount_filter = request.args.get("min_amount", "").strip()

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            """
            SELECT *
            FROM EmpPayRaise
            ORDER BY PayRaiseDate DESC, PayRaiseID DESC
            """
        )
        rows = cur.fetchall()

    decrypted = []

    for r in rows:
        raise_amount = float(dec(r["RaiseAmt"]))

        pay_raise = {
            "PayRaiseID": r["PayRaiseID"],
            "EmpID": r["EmpID"],
            "PayRaiseDate": r["PayRaiseDate"],
            "RaiseAmt": raise_amount,
            "IsVoided": r["IsVoided"],
            "Status": "Voided" if r["IsVoided"] == 1 else "Active",
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
# My Pay Raises
# --------------------------
@payraise_bp.route("/mypayraises")
def mypayraises():
    """Show active pay raises for the currently logged-in user."""
    guard = require_login()
    if guard:
        return guard

    uid = session["UserID"]

    with get_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (uid,),
        )
        employee = cur.fetchone()

        cur.execute(
            """
            SELECT PayRaiseDate, RaiseAmt
            FROM EmpPayRaise
            WHERE EmpID = ?
              AND IsVoided = 0
            ORDER BY PayRaiseDate DESC
            """,
            (uid,),
        )
        rows = cur.fetchall()

    current_salary = "Not set"
    if employee is not None and employee["CurrentSalary"] is not None:
        current_salary = f"${float(dec(employee['CurrentSalary'])):,.2f}"

    decrypted = []

    for r in rows:
        decrypted.append(
            {
                "PayRaiseDate": r["PayRaiseDate"],
                "RaiseAmt": float(dec(r["RaiseAmt"])),
            }
        )

    return render_template(
        "mypayraises.html",
        rows=decrypted,
        current_salary=current_salary,
    )


# --------------------------
# Submit Pay Raise Void Request
# --------------------------
@payraise_bp.route("/submitdeletepayraise", methods=["GET", "POST"])
def submitdeletepayraise():
    """
    Submit an encrypted request to void an active pay raise.

    The route keeps the original URL for compatibility, but the current behavior
    is voiding the record instead of permanently deleting it.
    """
    guard = require_level({1, 2})
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        date = request.form.get("PayRaiseDate", "").strip()

        emp_id_errors, emp_id_value = validate_employee_id(
            emp_id,
            numeric_message="EmpID must be a number.",
            require_positive=False,
        )

        errors = emp_id_errors
        errors.extend(validate_payraise_date(date, "PayRaiseDate"))

        if errors:
            return render_template("result.html", msg=", ".join(errors))

        with get_db() as con:
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM EmpPayRaise
                WHERE EmpID = ?
                  AND PayRaiseDate = ?
                  AND IsVoided = 0
                """,
                (emp_id_value, date),
            )
            row = cur.fetchone()

        if not row:
            return render_template(
                "result.html",
                msg="No active pay raise found for that EmpID and PayRaiseDate.",
            )

        body_text = f"{emp_id}{HMAC_SEPARATOR}{date}"
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
            sock.connect((VOID_HOST, VOID_PORT))
            sock.sendall(sent_message)
            sock.close()

            log_audit(
                "VOID_PAY_RAISE",
                f"Requested void for pay raise belonging to EmpID {emp_id} on {date}.",
            )

            return render_template(
                "result.html",
                msg="Void pay raise successfully sent.",
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - pay raise was NOT voided.",
            )

    return render_template("submitdeletepayraise.html")


# --------------------------
# Send HMAC Add Pay Raise Message
# --------------------------
@payraise_bp.route("/sendaddpayraisehmac", methods=["GET", "POST"])
def sendaddpayraisehmac():
    """
    Send an encrypted, HMAC-authenticated request to add a pay raise.

    The message body is encrypted before sending, and the plaintext body is
    signed with HMAC-SHA3-512 so the receiver can detect tampering.
    """
    guard = require_level({1, 2})
    if guard:
        return guard

    if request.method == "POST":
        emp_id = request.form.get("EmpID", "").strip()
        payraise_date = request.form.get("PayRaiseDate", "").strip()
        raise_amt = request.form.get("RaiseAmt", "").strip()

        emp_id_errors, emp_id_value = validate_employee_id(emp_id)
        errors = emp_id_errors

        if not emp_id_errors:
            with get_db() as con:
                con.row_factory = sql.Row
                cur = con.cursor()
                cur.execute(
                    "SELECT UserID FROM Employee WHERE UserID=?",
                    (emp_id_value,),
                )
                row = cur.fetchone()

            if not row:
                errors.append("EmpID does not exist in the Employee table.")

        errors.extend(validate_payraise_date(payraise_date, "PayRaiseDate"))

        amount_errors, _ = validate_raise_amount(raise_amt, "RaiseAmt")
        errors.extend(amount_errors)

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
                msg="Message to create a pay raise successfully sent.",
            )
        except OSError:
            return render_template(
                "result.html",
                msg="Error - message to create a pay raise NOT sent.",
            )

    return render_template("sendaddpayraisehmac.html")
