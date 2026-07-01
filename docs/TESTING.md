# Testing

The automated test suite uses `pytest` and currently contains 11 tests.

## Available Tests

- `tests/test_encryption.py` verifies encrypted values decrypt correctly and
  that repeated encryption uses fresh ciphertext.
- `tests/test_hmac.py` verifies both socket servers accept valid HMAC tags and
  reject messages that were changed after signing.
- `tests/test_salary_updates.py` verifies salary changes when pay raises are
  added or voided, missing-salary rejection, duplicate-void protection, and
  transaction rollback behavior.

Salary update tests create temporary databases and do not modify
`EmployeeDB.db`.

## Run Tests

From the project root, run the complete suite:

```bat
.venv\Scripts\python.exe -m pytest
```

Run one test file:

```bat
.venv\Scripts\python.exe -m pytest tests\test_encryption.py
.venv\Scripts\python.exe -m pytest tests\test_hmac.py
.venv\Scripts\python.exe -m pytest tests\test_salary_updates.py
```

If the virtual environment is already activated, `python` can be used instead:

```bat
python -m pytest
```
