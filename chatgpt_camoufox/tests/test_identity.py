"""Account identity fields must be plausible and formula-derived, not hardcoded."""
import random
from datetime import date

from chatgpt_camoufox import identity


def test_random_name_from_pools():
    name = identity.random_name(random.Random(0))
    first, last = name.split(" ")
    assert first in identity._FIRST
    assert last in identity._LAST


def test_random_name_varies():
    seen = {identity.random_name(random.Random(i)) for i in range(50)}
    assert len(seen) > 1


def test_birthdate_from_age_matches_ui_rule():
    # UI rule (verified in capture): today's year - age, same month/day.
    today = date(2026, 6, 26)
    assert identity.birthdate_from_age(44, today=today) == "1982-06-26"


def test_birthdate_from_age_pads_month_day():
    today = date(2026, 1, 5)
    assert identity.birthdate_from_age(20, today=today) == "2006-01-05"


def test_random_birthdate_within_age_range():
    today = date(2026, 6, 26)
    for i in range(100):
        bd = identity.random_birthdate(random.Random(i), min_age=19, max_age=55,
                                       today=today)
        year = int(bd.split("-")[0])
        age = today.year - year
        assert 19 <= age <= 55
        assert bd.endswith("-06-26")
