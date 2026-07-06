"""
Pay Raise Business Logic

Provides transactional operations for adding and voiding pay raises while
keeping employee current salary synchronized.
"""

import sqlite3

from crypto_helpers import dec, enc


class PayRaiseValidationError(Exception):
    """Raised when a pay raise operation violates a business rule."""


class PayRaiseDataError(Exception):
    """Raised when encrypted salary data cannot be interpreted."""


def add_pay_raise(db_name, emp_id, payraise_date, raise_amount):
    """Insert a pay raise and increase current salary in one transaction."""
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT UserID, CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        )
        employee = cur.fetchone()

        if not employee:
            raise PayRaiseValidationError(
                "EmpID does not exist in the Employee table."
            )

        encrypted_current_salary = employee[1]
        if encrypted_current_salary is None:
            raise PayRaiseValidationError("Employee current salary is not set.")

        try:
            current_salary = float(dec(encrypted_current_salary))
        except (TypeError, ValueError) as error:
            raise PayRaiseDataError(
                f"Employee current salary is invalid: {error}"
            ) from error

        updated_salary = current_salary + raise_amount

        cur.execute(
            """
            INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
            VALUES (?, ?, ?)
            """,
            (emp_id, payraise_date, enc(str(raise_amount))),
        )

        cur.execute(
            """
            UPDATE Employee
            SET CurrentSalary = ?
            WHERE UserID = ?
            """,
            (enc(f"{updated_salary:.2f}"), emp_id),
        )
        conn.commit()


def void_pay_raise(db_name, emp_id, payraise_date):
    """Void an active pay raise and decrease salary in one transaction."""
    with sqlite3.connect(db_name) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT EmpPayRaise.PayRaiseID,
                   EmpPayRaise.RaiseAmt,
                   Employee.CurrentSalary
            FROM EmpPayRaise
            JOIN Employee ON Employee.UserID = EmpPayRaise.EmpID
            WHERE EmpPayRaise.EmpID = ?
              AND EmpPayRaise.PayRaiseDate = ?
              AND EmpPayRaise.IsVoided = 0
            """,
            (emp_id, payraise_date),
        )
        pay_raise = cur.fetchone()

        if not pay_raise:
            raise PayRaiseValidationError(
                "No active matching EmpPayRaise record found "
                f"for EmpID={emp_id} and PayRaiseDate={payraise_date}."
            )

        payraise_id = pay_raise[0]
        encrypted_raise_amount = pay_raise[1]
        encrypted_current_salary = pay_raise[2]

        if encrypted_current_salary is None:
            raise PayRaiseValidationError("Employee current salary is not set.")

        try:
            raise_amount = float(dec(encrypted_raise_amount))
            current_salary = float(dec(encrypted_current_salary))
        except (TypeError, ValueError) as error:
            raise PayRaiseDataError(f"Salary data is invalid: {error}") from error

        updated_salary = current_salary - raise_amount

        if updated_salary < 0:
            raise PayRaiseValidationError(
                "Voiding this raise would make current salary negative."
            )

        cur.execute(
            """
            UPDATE EmpPayRaise
            SET IsVoided = 1
            WHERE PayRaiseID = ?
            """,
            (payraise_id,),
        )

        cur.execute(
            """
            UPDATE Employee
            SET CurrentSalary = ?
            WHERE UserID = ?
            """,
            (enc(f"{updated_salary:.2f}"), emp_id),
        )
        conn.commit()
