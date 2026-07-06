"""
Encrypted Pay Raise Void Server

TCP server that receives encrypted, HMAC-authenticated pay raise void
requests, decrypts each message, validates the request, and marks the matching
pay raise record as voided in the local SQLite database.

The filename still uses "Deletions" for compatibility with the existing
project scripts and README, but the current behavior is voiding records instead
of permanently deleting them.
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
    void_pay_raise,
)
from validation_helpers import validate_payraise_date

DB_NAME = "EmployeeDB.db"
HOST = "localhost"
PORT = 9999
HMAC_TAG_LEN = 64
SEPARATOR = "^%$"


def verify_hmac(message_bytes: bytes, tag: bytes) -> bool:
    """Return True when the HMAC tag matches the plaintext message bytes."""
    expected_tag = hmac.new(
        HMAC_SECRET,
        message_bytes,
        digestmod=hashlib.sha3_512,
    ).digest()

    return hmac.compare_digest(tag, expected_tag)


class PayRaiseVoidHandler(socketserver.BaseRequestHandler):
    """
    Handle one encrypted, HMAC-authenticated pay raise void request.

    Expected decrypted message format:
    EmpID^%$PayRaiseDate
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
            plain_text = Encryption.cipher.decrypt(encrypted_message)
        except Exception as error:
            print(f"Decryption error: {error}")
            return

        print(f"Decrypted message: {plain_text}")

        message_bytes = plain_text.encode("utf-8")
        if not verify_hmac(message_bytes, tag):
            print("Authentication failed: HMAC verification did not match.")
            return

        if SEPARATOR not in plain_text:
            print("Validation error: Message is missing the separator.")
            return

        emp_id_text, payraise_date = plain_text.split(SEPARATOR, 1)
        emp_id_text = emp_id_text.strip()
        payraise_date = payraise_date.strip()

        print(f"EmpID: {emp_id_text}")
        print(f"PayRaiseDate: {payraise_date}")

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

        try:
            void_pay_raise(DB_NAME, emp_id, payraise_date)

            print("Record successfully voided.")

        except PayRaiseValidationError as error:
            print(f"Validation error: {error}")
        except PayRaiseDataError as error:
            print(f"Data error: {error}")
        except sqlite3.Error as error:
            print(f"Database error: {error}")


if __name__ == "__main__":
    try:
        print(f"Starting Pay Raise Void Server on {HOST}:{PORT} ...")
        with socketserver.TCPServer((HOST, PORT), PayRaiseVoidHandler) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    except OSError as error:
        print(f"Socket error: {error}")
