import json
from datetime import date
from pathlib import Path

from src.part_a import DUPLICATE_REASON, clean_articles, count_by_topic_week, parse_date

# The assignment's five articles, loaded from the same file main() uses.
DATA = json.loads(
    (Path(__file__).parent.parent / "data" / "articles.json").read_text(
        encoding="utf-8"
    )
)

# Constructed edge cases (not the assignment data): a duplicate whose title is in
# a different casing with a slash date, and a Monday/Sunday pair in one ISO week.
FIXTURES = [
    {
        "title": "City Council Approves New Transit Line",
        "topic": "local",
        "date": "2026-08-01",
    },
    {
        "title": "CITY COUNCIL APPROVES NEW TRANSIT LINE",
        "topic": "Local",
        "date": "08/01/2026",
    },
    {"title": "Budget Vote Delayed", "topic": "local", "date": "2026-08-03"},
    {"title": "Late Local Roundup", "topic": "Local", "date": "2026-08-09"},
]


def test_slash_date_is_read_month_first():
    """08/01/2026 is 1 August 2026, not 8 January."""
    assert parse_date("08/01/2026") == date(2026, 8, 1)


def test_duplicate_with_different_casing_is_removed():
    """The same title and date in different casing collapses to one record."""
    cleaned, rejected = clean_articles(FIXTURES[:2])

    assert len(cleaned) == 1
    assert cleaned[0]["title"] == "City Council Approves New Transit Line"
    assert cleaned[0]["date"] == date(2026, 8, 1)

    assert len(rejected) == 1
    assert rejected[0][1].startswith(DUPLICATE_REASON)


def test_sunday_counts_in_the_week_that_started_on_monday():
    """9 August is a Sunday, so it belongs to the ISO week starting 3 August."""
    assert date(2026, 8, 9).isoweekday() == 7

    cleaned, _ = clean_articles(FIXTURES[2:4])
    rows = count_by_topic_week(cleaned)

    assert rows == [
        {
            "topic": "local",
            "iso_year": 2026,
            "iso_week": 32,
            "week_start": date(2026, 8, 3),
            "count": 2,
        }
    ]


def test_assignment_data_gives_expected_counts():
    """The assignment's five rows: one duplicate removed, three (topic, week) tallies."""
    cleaned, rejected = clean_articles(DATA)
    rows = count_by_topic_week(cleaned)

    assert len(cleaned) == 4
    assert len(rejected) == 1
    assert [(r["topic"], r["iso_week"], r["count"]) for r in rows] == [
        ("local", 31, 1),
        ("business", 32, 2),
        ("sports", 32, 1),
    ]
