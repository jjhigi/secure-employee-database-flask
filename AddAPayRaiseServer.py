"""
Authenticated Pay Raise Creation Server

TCP server that receives encrypted pay raise creation messages, verifies the
HMAC signature, validates the request, and inserts new pay raise records into
the local SQLite database.
"""

import hashlib
import hmac
import socketserver
import sqlite3
from datetime import datetime

import Encryption
from config import HMAC_SECRET

DB_NAME = "EmployeeDB.db"
HOST = "localhost"
PORT = 8888

HMAC_TAG_LEN = 64
HMAC_SEPARATOR = "^%$"


def enc(value: str) -> str:
    """Encrypt a string for SQLite storage."""
    return Encryption.cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def dec(value: str) -> str:
    """Decrypt a stored SQLite value back into a string."""
    return Encryption.cipher.decrypt(value)


def verify_hmac(message_bytes: bytes, tag: bytes) -> bool:
    """Return True when the HMAC tag matches the plaintext message bytes."""
    expected_tag = hmac.new(
        HMAC_SECRET,
        message_bytes,
        digestmod=hashlib.sha3_512,
    ).digest()

    return hmac.compare_digest(tag, expected_tag)


class AddPayRaiseHandler(socketserver.BaseRequestHandler):
    """
    Handle one encrypted, HMAC-authenticated add-pay-raise request.

    Expected decrypted message format:
    EmpID^%$PayRaiseDate^%$RaiseAmt
    """

    def handle(self):
        data = self.request.recv(2048)
        client_ip = self.client_address[0]

        print(f"{client_ip} sent message:")
        print(data)

        if not data:
            print("Validation error: No data received.")
            return

        if len(data) <= HMAC_TAG_LEN:
            print("Validation error: Message too short to contain an HMAC tag.")
            return

        encrypted_message = data[:-HMAC_TAG_LEN]
        tag = data[-HMAC_TAG_LEN:]

        try:
            plaintext = Encryption.cipher.decrypt(encrypted_message)
        except Exception as error:
            print(f"Decryption error: {error}")
            return

        print(f"Decrypted message: {plaintext}")

        message_bytes = plaintext.encode("utf-8")
        if not verify_hmac(message_bytes, tag):
            print("Authentication failed: HMAC verification did not match.")
            return

        parts = plaintext.split(HMAC_SEPARATOR)
        if len(parts) != 3:
            print(
                "Validation error: Message format incorrect. "
                "Expected EmpID, PayRaiseDate, and RaiseAmt."
            )
            return

        emp_id_text = parts[0].strip()
        payraise_date = parts[1].strip()
        raise_amt_text = parts[2].strip()

        try:
            emp_id = int(emp_id_text)
        except ValueError:
            print("Validation error: EmpID is not a valid integer.")
            return

        if emp_id <= 0:
            print("Validation error: EmpID must be a positive integer.")
            return

        try:
            datetime.strptime(payraise_date, "%Y-%m-%d")
        except ValueError:
            print("Validation error: PayRaiseDate must be in YYYY-MM-DD format.")
            return

        try:
            raise_amt = float(raise_amt_text)
        except ValueError:
            print("Validation error: RaiseAmt is not a valid numeric value.")
            return

        if raise_amt <= 0:
            print("Validation error: RaiseAmt must be greater than 0.")
            return

        try:
            with sqlite3.connect(DB_NAME) as conn:
                cur = conn.cursor()

                cur.execute(
                    "SELECT UserID, CurrentSalary FROM Employee WHERE UserID=?",
                    (emp_id,),
                )
                row = cur.fetchone()

                if not row:
                    print("Validation error: EmpID does not exist in the Employee table.")
                    return

                if row[1] is None:
                    print("Validation error: Employee current salary is not set.")
                    return

                try:
                    current_salary = float(dec(row[1]))
                except (TypeError, ValueError) as error:
                    print(f"Data error: Employee current salary is invalid: {error}")
                    return

                updated_salary = current_salary + raise_amt

                cur.execute(
                    """
                    INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
                    VALUES (?, ?, ?)
                    """,
                    (emp_id, payraise_date, enc(str(raise_amt))),
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

            print(f"EmpID: {emp_id}")
            print("Record successfully added.")

        except sqlite3.Error as error:
            print(f"Database error: {error}")


if __name__ == "__main__":
    try:
        print(f"Starting Add Pay Raise HMAC Server on {HOST}:{PORT} ...")
        with socketserver.TCPServer((HOST, PORT), AddPayRaiseHandler) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    except OSError as error:
        print(f"Socket error: {error}")
