"""
Encrypted Pay Raise Deletion Server

TCP server that receives encrypted pay raise void requests,
decrypts the message, validates the request, and marks matching
records as voided in the SQLite database.
"""

import socketserver
import sqlite3
from datetime import datetime
import Encryption

SEPARATOR = "^%$"
DB_NAME = "EmployeeDB.db"
HOST, PORT = "localhost", 9999


def dec(s: str) -> str:
    """Decrypt text (string) into a normal Python string."""
    return Encryption.cipher.decrypt(s)


class PayRaiseDeleteHandler(socketserver.BaseRequestHandler):
    """
    Handles a single delete request:
      1. Receives an encrypted message from the client.
      2. Decrypts to get "EmpID^%$PayRaiseDate".
      3. Validates fields and the existence of the record.
      4. Marks the matching EmpPayRaise record as voided if valid.
      5. Prints clear messages about what happened.
    """

    def handle(self):
        # Receive up to 1024 bytes from client
        data = self.request.recv(1024).strip()
        client_ip = self.client_address[0]

        print(f"{client_ip} sent message:")
        print(data)

        if not data:
            print("Validation error: No data received.")
            return

        # Decrypt the incoming message
        try:
            encrypted_text = data.decode("utf-8")
        except UnicodeDecodeError:
            print("Validation error: Received bytes could not be decoded as UTF-8.")
            return

        try:
            plain_text = dec(encrypted_text)
        except Exception as e:
            print(f"Decryption error: {e}")
            return

        print(f"Decrypted message: {plain_text}")

        # Expect format: "EmpID^%$PayRaiseDate"
        if SEPARATOR not in plain_text:
            print("Validation error: Message is missing the separator.")
            return

        emp_id_str, payraise_date = plain_text.split(SEPARATOR, 1)
        emp_id_str = emp_id_str.strip()
        payraise_date = payraise_date.strip()

        print(f"EmpID: {emp_id_str}")
        print(f"PayRaiseDate: {payraise_date}")

        # Validate EmpID is an integer
        try:
            emp_id = int(emp_id_str)
            if emp_id <= 0:
                print("Validation error: EmpID must be a positive integer.")
                return
        except ValueError:
            print("Validation error: EmpID is not a valid integer.")
            return

        # Validate date format
        try:
            datetime.strptime(payraise_date, "%Y-%m-%d")
        except ValueError:
            print("Validation error: PayRaiseDate must be in YYYY-MM-DD format.")
            return

        # Connect to the database and check for matching record
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            cur.execute(
                """
                SELECT PayRaiseID
                FROM EmpPayRaise
                WHERE EmpID = ?
                  AND PayRaiseDate = ?
                  AND IsVoided = 0
                """,
                (emp_id, payraise_date),
            )
            row = cur.fetchone()

            if not row:
                print(
                    "Validation error: No active matching EmpPayRaise record found "
                    f"for EmpID={emp_id} and PayRaiseDate={payraise_date}."
                )
                conn.close()
                return

            payraise_id = row[0]

            # Void the record instead of deleting it
            cur.execute(
                "UPDATE EmpPayRaise SET IsVoided=1 WHERE PayRaiseID=?",
                (payraise_id,),
            )
            conn.commit()
            conn.close()

            print("Record successfully voided.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")


if __name__ == "__main__":
    try:
        print(f"Starting Pay Raise Deletion Server on {HOST}:{PORT} ...")
        with socketserver.TCPServer((HOST, PORT), PayRaiseDeleteHandler) as server:
            # This will run until you stop it
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down (KeyboardInterrupt).")
    except OSError as e:
        print(f"Socket error: {e}")
