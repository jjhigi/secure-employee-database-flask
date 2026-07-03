"""
Shared Input Validation Helpers

Provides plain validation functions for Flask routes and socket servers.
These helpers do not access Flask state, databases, or encryption services.
"""

from datetime import datetime

from validation_constants import (
    MAX_NAME_LENGTH,
    MAX_PASSWORD_LENGTH,
    MAX_PHONE_LENGTH,
    MAX_RAISE_AMOUNT,
    MAX_SALARY,
    MIN_PASSWORD_LENGTH,
)


def validate_name(value):
    """Validate and normalize an employee name."""
    value = value.strip()
    errors = []

    if not value:
        errors.append("Name cannot be empty.")
    elif len(value) > MAX_NAME_LENGTH:
        errors.append(f"Name cannot be longer than {MAX_NAME_LENGTH} characters.")

    return errors, value


def validate_age(value):
    """Validate an employee age and return its integer value."""
    value = value.strip()

    if not value.isdigit() or not (1 <= int(value) <= 120):
        return ["Age must be 1-120."], None

    return [], int(value)


def validate_phone(value):
    """Validate and normalize an employee phone number."""
    value = value.strip()
    errors = []

    if not value:
        errors.append("Phone number cannot be empty.")
    elif len(value) > MAX_PHONE_LENGTH:
        errors.append(
            f"Phone number cannot be longer than {MAX_PHONE_LENGTH} characters."
        )

    return errors, value


def validate_salary(value):
    """Validate a current salary and return its numeric value."""
    value = value.strip()

    try:
        salary_value = float(value)
    except ValueError:
        return ["Current salary must be a valid number."], None

    if salary_value <= 0:
        return ["Current salary must be greater than 0."], salary_value

    if salary_value > MAX_SALARY:
        return [
            f"Current salary cannot be more than ${MAX_SALARY:,.2f}."
        ], salary_value

    return [], salary_value


def validate_security_level(value):
    """Validate a security level and return its integer value."""
    value = value.strip()

    if not value.isdigit() or not (1 <= int(value) <= 3):
        return [
            "Security level must be 1 (Admin), 2 (Manager), or 3 (Employee)."
        ], None

    return [], int(value)


def validate_password(
    password,
    confirmation,
    field_name="Password",
    mismatch_message="Passwords do not match.",
):
    """Validate and normalize a password plus its confirmation."""
    password = password.strip()
    confirmation = confirmation.strip()
    errors = []

    if not password:
        errors.append(f"{field_name} cannot be empty.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors.append(
            f"{field_name} must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors.append(
            f"{field_name} cannot be longer than {MAX_PASSWORD_LENGTH} characters."
        )

    if password != confirmation:
        errors.append(mismatch_message)

    return errors, password


def validate_employee_id(
    value,
    numeric_message="EmpID must be a numeric value.",
    require_positive=True,
):
    """Validate an employee ID and return its integer value."""
    value = value.strip()

    if not value:
        return ["EmpID is required."], None

    if not value.isdigit():
        return [numeric_message], None

    employee_id = int(value)

    if require_positive and employee_id <= 0:
        return ["EmpID must be greater than 0."], None

    return [], employee_id


def validate_payraise_date(date_text, field_name):
    """Validate a pay raise date and return a list of error messages."""
    errors = []

    if not date_text:
        errors.append(f"{field_name} is required.")
        return errors

    try:
        date_value = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        errors.append(f"{field_name} must be a valid date in YYYY-MM-DD format.")
        return errors

    earliest_allowed_date = datetime.strptime("2000-01-01", "%Y-%m-%d").date()
    today = datetime.today().date()

    if date_value < earliest_allowed_date:
        errors.append(f"{field_name} cannot be before 2000-01-01.")
    elif date_value > today:
        errors.append(f"{field_name} cannot be in the future.")

    return errors


def validate_raise_amount(amount_text, field_name):
    """Validate a raise amount and return errors plus its numeric value."""
    errors = []
    amount_value = None

    if not amount_text:
        errors.append(f"{field_name} is required.")
        return errors, amount_value

    try:
        amount_value = float(amount_text)
    except ValueError:
        errors.append(f"{field_name} must be a numeric value.")
        return errors, amount_value

    if amount_value <= 0:
        errors.append(f"{field_name} must be greater than 0.")
    elif amount_value > MAX_RAISE_AMOUNT:
        errors.append(f"{field_name} cannot be more than ${MAX_RAISE_AMOUNT:,.2f}.")

    return errors, amount_value
