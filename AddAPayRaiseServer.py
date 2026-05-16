"""
Authenticated Pay Raise Creation Server

TCP server that receives encrypted pay raise creation messages,
verifies the HMAC signature, validates the request, and inserts
new pay raise records into the SQLite database.
"""

import socketserver
import sqlite3
from datetime import datetime
import hmac
from config import HMAC_SECRET
import hashlib
import Encryption

DB_NAME = "EmployeeDB.db"
HOST, PORT = "localhost", 8888

HMAC_TAG_LEN = 64  # sha3_512 digest length
HMAC_SEPARATOR = "^%$"  # same separator used by the client


def enc(s: str) -> str:
    """Encrypt a Python string and return text for storage."""
    return Encryption.cipher.encrypt(s.encode("utf-8")).decode("utf-8")


def verify_hmac(message_bytes: bytes, sig: bytes) -> bool:
    """
    Compute HMAC over message_bytes and compare to sig.
    Returns True if the tag matches, False otherwise.
    """
    computed = hmac.new(
        HMAC_SECRET,
        message_bytes,
        digestmod=hashlib.sha3_512
    ).digest()
    return sig == computed


class AddPayRaiseHandler(socketserver.BaseRequestHandler):
    """
    Handles a single add-pay-raise request:
      1. Receives ciphertext + HMAC tag from the client.
      2. Splits off the last 64 bytes as the tag.
      3. Decrypts the ciphertext portion to recover the plaintext.
      4. Verifies the HMAC over the plaintext.
      5. If authenticated, parses EmpID, PayRaiseDate, RaiseAmt.
      6. Validates all fields and inserts a new EmpPayRaise record if valid.
      7. Prints clear messages about what happened.
    """

    def handle(self):
        data = self.request.recv(2048).strip()
        client_ip = self.client_address[0]

        print(f"{client_ip} sent message:")
        print(data)

        if not data:
            print("Validation error: No data received.")
            return

        if len(data) <= HMAC_TAG_LEN:
            print("Validation error: Message too short to contain an HMAC tag.")
            return

        # Split into ciphertext and tag
        message_encrypted = data[:-HMAC_TAG_LEN]
        tag = data[-HMAC_TAG_LEN:]

        # Decrypt ciphertext
        try:
            # Encryption.cipher.decrypt returns a UTF-8 string
            plaintext = Encryption.cipher.decrypt(message_encrypted)
        except Exception as e:
            print(f"Decryption error: {e}")
            return

        print(f"Decrypted message: {plaintext}")

        # Verify HMAC over the plaintext bytes
        message_bytes = plaintext.encode("utf-8")
        if not verify_hmac(message_bytes, tag):
            print("Authentication failed: HMAC verification did not match.")
            return

        # Split plaintext into fields: EmpID, PayRaiseDate, RaiseAmt
        parts = plaintext.split(HMAC_SEPARATOR)
        if len(parts) != 3:
            print("Validation error: Message format incorrect. "
                  "Expected three fields separated by the separator.")
            return

        emp_id_str = parts[0].strip()
        payraise_date = parts[1].strip()
        raise_amt_str = parts[2].strip()

        # Validate EmpID
        try:
            emp_id = int(emp_id_str)
            if emp_id <= 0:
                print("Validation error: EmpID must be a positive integer.")
                return
        except ValueError:
            print("Validation error: EmpID is not a valid integer.")
            return

        # Validate PayRaiseDate
        try:
            datetime.strptime(payraise_date, "%Y-%m-%d")
        except ValueError:
            print("Validation error: PayRaiseDate must be in YYYY-MM-DD format.")
            return

        # Validate RaiseAmt
        try:
            amt = float(raise_amt_str)
            if amt <= 0:
                print("Validation error: RaiseAmt must be greater than 0.")
                return
        except ValueError:
            print("Validation error: RaiseAmt is not a valid numeric value.")
            return

        # Connect to database and validate EmpID exists, then insert record
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # Check EmpID exists in Employee table
            cur.execute(
                "SELECT UserID FROM Employee WHERE UserID=?",
                (emp_id,),
            )
            row = cur.fetchone()
            if not row:
                print("Validation error: EmpID does not exist in the Employee table.")
                conn.close()
                return

            # Encrypt RaiseAmt for storage
            enc_raise_amt = enc(str(amt))

            # Insert new EmpPayRaise record
            cur.execute(
                """
                INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
                VALUES (?, ?, ?)
                """,
                (emp_id, payraise_date, enc_raise_amt),
            )
            conn.commit()
            conn.close()

            print(f"empID: {emp_id}")
            print("Record successfully added")

        except sqlite3.Error as e:
            print(f"Database error: {e}")


if __name__ == "__main__":
    try:
        print(f"Starting Add a Pay Raise HMAC Server on {HOST}:{PORT} ...")
        with socketserver.TCPServer((HOST, PORT), AddPayRaiseHandler) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down (KeyboardInterrupt).")
    except OSError as e:
        print(f"Socket error: {e}")
