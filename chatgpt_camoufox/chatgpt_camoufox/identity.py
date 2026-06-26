"""Generate plausible, non-hardcoded account identity fields (name, birthdate).

`birthdate` is derived from an age the same way the signup UI does: it takes
today's date and subtracts the age from the year, keeping month/day. Verified
against the capture (request 2026-06-26, birthdate "1982-06-26" -> age 44, same
month-day as the request date).
"""
from __future__ import annotations

import random
from datetime import date

_FIRST = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie",
    "Minh", "Anh", "Huy", "Linh", "Nam", "Trang", "Khoa", "Mai", "Yến", "Như",
]
_LAST = [
    "Nguyen", "Tran", "Le", "Pham", "Smith", "Johnson", "Brown", "Garcia",
    "Vu", "Dang", "Bui", "Do", "Ho", "Ngo", "Duong", "Ly",
]


def random_name(rng: random.Random | None = None) -> str:
    rng = rng or random
    return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"


def birthdate_from_age(age: int, today: date | None = None) -> str:
    """birthdate = today with year -= age (month/day unchanged), like the UI."""
    today = today or date.today()
    return f"{today.year - age:04d}-{today.month:02d}-{today.day:02d}"


def random_birthdate(rng: random.Random | None = None,
                     min_age: int = 19, max_age: int = 55,
                     today: date | None = None) -> str:
    rng = rng or random
    return birthdate_from_age(rng.randint(min_age, max_age), today=today)
