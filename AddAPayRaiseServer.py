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

import Encryption
from config import HMAC_SECRET
from payraise_service import (
    PayRaiseDataError,
    PayRaiseValidationError,
    add_pay_raise,
)
from validation_helpers import validate_payraise_date, validate_raise_amount

DB_NAME = "EmployeeDB.db"
HOST = "localhost"
PORT = 8888

HMAC_TAG_LEN = 64
HMAC_SEPARATOR = "^%$"


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

        date_errors = validate_payraise_date(payraise_date, "PayRaiseDate")
        if date_errors:
            print(f"Validation error: {', '.join(date_errors)}")
            return

        amount_errors, raise_amt = validate_raise_amount(
            raise_amt_text,
            "RaiseAmt",
        )
        if amount_errors:
            print(f"Validation error: {', '.join(amount_errors)}")
            return

        try:
            add_pay_raise(DB_NAME, emp_id, payraise_date, raise_amt)

            print(f"EmpID: {emp_id}")
            print("Record successfully added.")

        except PayRaiseValidationError as error:
            print(f"Validation error: {error}")
        except PayRaiseDataError as error:
            print(f"Data error: {error}")
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
