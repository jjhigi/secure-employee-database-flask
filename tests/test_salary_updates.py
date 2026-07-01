import hashlib
import hmac
import sqlite3

import pytest

import AddAPayRaiseServer
import Encryption
import ProcessPayRaiseDeletionsServer
import init_db
from config import HMAC_SECRET


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def recv(self, _size):
        return self.payload


def send_authenticated_message(handler_class, plaintext):
    message = plaintext.encode("utf-8")
    tag = hmac.new(HMAC_SECRET, message, digestmod=hashlib.sha3_512).digest()
    payload = Encryption.cipher.encrypt(message) + tag

    handler_class(FakeRequest(payload), ("127.0.0.1", 5000), object())


def enc(value):
    return Encryption.cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def dec(value):
    return Encryption.cipher.decrypt(value)


@pytest.fixture
def salary_db(tmp_path, monkeypatch):
    db_path = tmp_path / "salary_updates.db"

    monkeypatch.setattr(init_db, "DB_NAME", str(db_path))
    monkeypatch.setattr(AddAPayRaiseServer, "DB_NAME", str(db_path))
    monkeypatch.setattr(ProcessPayRaiseDeletionsServer, "DB_NAME", str(db_path))
    init_db.create_tables()

    return db_path


def insert_employee(db_path, current_salary):
    encrypted_salary = enc(current_salary) if current_salary is not None else None

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Employee
                (Name, Age, PhNum, CurrentSalary, SecurityLevel, PasswordHash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (enc("Test Employee"), 30, enc("5550100"), encrypted_salary, 3, "hash"),
        )
        return cur.lastrowid


def insert_raise(db_path, emp_id, date, amount):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO EmpPayRaise (EmpID, PayRaiseDate, RaiseAmt)
            VALUES (?, ?, ?)
            """,
            (emp_id, date, enc(amount)),
        )
        return cur.lastrowid


def test_add_raise_increases_salary_and_inserts_record(salary_db):
    emp_id = insert_employee(salary_db, "50000.00")

    send_authenticated_message(
        AddAPayRaiseServer.AddPayRaiseHandler,
        f"{emp_id}^%$2026-07-01^%$125.50",
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        raise_row = conn.execute(
            "SELECT RaiseAmt, IsVoided FROM EmpPayRaise WHERE EmpID = ?",
            (emp_id,),
        ).fetchone()

    assert salary != "50125.50"
    assert dec(salary) == "50125.50"
    assert float(dec(raise_row[0])) == 125.50
    assert raise_row[1] == 0


def test_add_raise_rejects_employee_without_salary(salary_db):
    emp_id = insert_employee(salary_db, None)

    send_authenticated_message(
        AddAPayRaiseServer.AddPayRaiseHandler,
        f"{emp_id}^%$2026-07-01^%$125.50",
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        raise_count = conn.execute(
            "SELECT COUNT(*) FROM EmpPayRaise WHERE EmpID = ?",
            (emp_id,),
        ).fetchone()[0]

    assert salary is None
    assert raise_count == 0


def test_void_raise_decreases_salary_only_once(salary_db):
    emp_id = insert_employee(salary_db, "50125.50")
    raise_id = insert_raise(salary_db, emp_id, "2026-07-01", "125.50")
    message = f"{emp_id}^%$2026-07-01"

    send_authenticated_message(
        ProcessPayRaiseDeletionsServer.PayRaiseVoidHandler,
        message,
    )
    send_authenticated_message(
        ProcessPayRaiseDeletionsServer.PayRaiseVoidHandler,
        message,
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        is_voided = conn.execute(
            "SELECT IsVoided FROM EmpPayRaise WHERE PayRaiseID = ?",
            (raise_id,),
        ).fetchone()[0]

    assert dec(salary) == "50000.00"
    assert is_voided == 1


def test_void_raise_rejects_employee_without_salary(salary_db):
    emp_id = insert_employee(salary_db, None)
    raise_id = insert_raise(salary_db, emp_id, "2026-07-01", "125.50")

    send_authenticated_message(
        ProcessPayRaiseDeletionsServer.PayRaiseVoidHandler,
        f"{emp_id}^%$2026-07-01",
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        is_voided = conn.execute(
            "SELECT IsVoided FROM EmpPayRaise WHERE PayRaiseID = ?",
            (raise_id,),
        ).fetchone()[0]

    assert salary is None
    assert is_voided == 0


def test_add_raise_rolls_back_when_salary_update_fails(salary_db):
    emp_id = insert_employee(salary_db, "50000.00")

    with sqlite3.connect(salary_db) as conn:
        conn.execute(
            """
            CREATE TRIGGER block_salary_update
            BEFORE UPDATE OF CurrentSalary ON Employee
            BEGIN
                SELECT RAISE(ABORT, 'blocked salary update');
            END
            """
        )

    send_authenticated_message(
        AddAPayRaiseServer.AddPayRaiseHandler,
        f"{emp_id}^%$2026-07-01^%$125.50",
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        raise_count = conn.execute(
            "SELECT COUNT(*) FROM EmpPayRaise WHERE EmpID = ?",
            (emp_id,),
        ).fetchone()[0]

    assert dec(salary) == "50000.00"
    assert raise_count == 0


def test_void_raise_rolls_back_when_salary_update_fails(salary_db):
    emp_id = insert_employee(salary_db, "50125.50")
    raise_id = insert_raise(salary_db, emp_id, "2026-07-01", "125.50")

    with sqlite3.connect(salary_db) as conn:
        conn.execute(
            """
            CREATE TRIGGER block_salary_update
            BEFORE UPDATE OF CurrentSalary ON Employee
            BEGIN
                SELECT RAISE(ABORT, 'blocked salary update');
            END
            """
        )

    send_authenticated_message(
        ProcessPayRaiseDeletionsServer.PayRaiseVoidHandler,
        f"{emp_id}^%$2026-07-01",
    )

    with sqlite3.connect(salary_db) as conn:
        salary = conn.execute(
            "SELECT CurrentSalary FROM Employee WHERE UserID = ?",
            (emp_id,),
        ).fetchone()[0]
        is_voided = conn.execute(
            "SELECT IsVoided FROM EmpPayRaise WHERE PayRaiseID = ?",
            (raise_id,),
        ).fetchone()[0]

    assert dec(salary) == "50125.50"
    assert is_voided == 0
