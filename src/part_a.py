import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path

# Accepted date formats, tried in order.
# Slash dates are read month-first (MM/DD/YYYY): in the sample data,
# "08/01/2026" duplicates an article dated 2026-08-01.
DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")

# Field names expected on each raw article record.
DATE_KEY = "date"
TITLE_KEY = "title"
TOPIC_KEY = "topic"

# Prefix for rejection reasons that mark a duplicate (used by the report).
DUPLICATE_REASON = "Duplicate"  # changed


def parse_date(raw: str, formats: tuple[str, ...] = DATE_FORMATS) -> date:
    """Parse a date string into a date, trying each format in ``formats`` in order.

    Surrounding whitespace is ignored.

    Raises:
        TypeError: if ``raw`` is not a string (e.g. a missing date, ``None``).
        ValueError: if ``raw`` matches none of the formats. Callers decide
            whether to skip and report the row or to stop.
    """

    if not isinstance(raw, str):
        raise TypeError(f"Expected a date string, got {type(raw).__name__}")

    cleaned = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Date format not recognized: {raw}")


def clean_articles(
    articles: list[dict],
    formats: tuple[str, ...] = DATE_FORMATS,
) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Normalise records and drop duplicates (same case-insensitive title and date).

    Returns (clean records, rejected records with a reason). Rows with an
    unparseable date or no title are rejected; a missing topic becomes "unknown".
    """

    cleaned: list[dict] = []
    rejected: list[tuple[dict, str]] = []
    seen: set[tuple[str, date]] = set()

    for article in articles:
        try:
            parsed = parse_date(article.get(DATE_KEY), formats)
        except (TypeError, ValueError) as exc:
            rejected.append((article, str(exc)))
            continue

        raw_title = article.get(TITLE_KEY)

        if not isinstance(raw_title, str) or not raw_title.strip():
            rejected.append((article, "Missing or empty title"))
            continue
        title = raw_title.strip()

        key = (title.casefold(), parsed)
        if key in seen:
            rejected.append(
                (
                    article,
                    f"{DUPLICATE_REASON} of earlier article dated {parsed}",
                )
            )
            continue

        raw_topic = article.get(TOPIC_KEY)
        topic = (
            raw_topic.strip().lower()
            if isinstance(raw_topic, str) and raw_topic.strip()
            else "unknown"
        )

        seen.add(key)
        record = {**article, DATE_KEY: parsed}
        record[TITLE_KEY] = title
        record[TOPIC_KEY] = topic
        cleaned.append(record)

    return cleaned, rejected


def count_by_topic_week(articles: list[dict]) -> list[dict]:
    """Tally clean articles by topic and ISO week, sorted in date order."""

    counts: Counter[tuple[str, int, int]] = Counter()
    for record in articles:
        iso_year, iso_week, _ = record[DATE_KEY].isocalendar()
        counts[(record[TOPIC_KEY], iso_year, iso_week)] += 1

    rows = [
        {
            TOPIC_KEY: topic,
            "iso_year": iso_year,
            "iso_week": iso_week,
            "week_start": date.fromisocalendar(iso_year, iso_week, 1),
            "count": count,
        }
        for (topic, iso_year, iso_week), count in counts.items()
    ]
    rows.sort(key=lambda row: (row["iso_year"], row["iso_week"], row[TOPIC_KEY]))
    return rows


def main() -> None:
    """Load the article data, clean it, and report weekly counts per topic."""

    path = Path(__file__).parent.parent / "data" / "articles.json"
    with path.open(encoding="utf-8") as handle:
        articles = json.load(handle)

    cleaned, rejected = clean_articles(articles)
    rows = count_by_topic_week(cleaned)

    print(f"Counts by topic and ISO week ({len(cleaned)} clean articles)")
    for row in rows:
        print(
            f"  {row['week_start']}  {row['iso_year']}-W{row['iso_week']:02d}  "
            f"{row[TOPIC_KEY]:<12} {row['count']:>3}"
        )

    duplicates = [item for item in rejected if item[1].startswith(DUPLICATE_REASON)]
    invalid = [item for item in rejected if not item[1].startswith(DUPLICATE_REASON)]

    print(f"\nDuplicates removed: {len(duplicates)}")
    for article, _ in duplicates:
        print(f"  {article.get(TITLE_KEY, '<no title>')}")

    print(f"\nInvalid rows: {len(invalid)}")
    for article, reason in invalid:
        print(f"  {reason} -> {article}")


if __name__ == "__main__":
    main()
