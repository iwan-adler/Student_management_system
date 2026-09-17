"""Input validation used by the GUI before data reaches SQLite."""

import re
from datetime import datetime


def required(value: str, label: str) -> str | None:
    return f"{label} is required." if not value.strip() else None


def valid_email(value: str) -> bool:
    return not value or bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def valid_phone(value: str) -> bool:
    return not value or bool(re.fullmatch(r"[0-9+()\-\s]{7,20}", value))


def valid_date(value: str) -> bool:
    if not value:
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False
