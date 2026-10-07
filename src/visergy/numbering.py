"""Gap-free, never-reused document numbers, continuing the conventions Visergy used in 2014-2018.

Numbers come from the `counters` table and MUST be allocated inside the same transaction that
issues the document. If that transaction rolls back (for example the PDF fails to render), the
counter rolls back with it, so no number is burned. Voided documents keep their numbers.

* Projects: four digits, one sequence that never resets ("0059"). The old projects ended at 0058,
  so the counter is seeded once with `seed_counter(conn, PROJECT_COUNTER, 58)`.
* Quotes and invoices share one sequence per calendar year: two-digit year plus a three-digit
  count ("26001", "26002", ...). The old numbers were all "14xxx", so they can never collide.
* Reports: per project, "0059-R01".
"""

from __future__ import annotations

import sqlite3

PROJECT_COUNTER = "project"


def _require_transaction(conn: sqlite3.Connection) -> None:
    if not conn.in_transaction:
        raise RuntimeError("allocate numbers inside a transaction (db.transaction)")


def next_value(conn: sqlite3.Connection, key: str) -> int:
    _require_transaction(conn)
    conn.execute(
        "INSERT INTO counters (key, value) VALUES (?, 0) ON CONFLICT (key) DO NOTHING", (key,)
    )
    conn.execute("UPDATE counters SET value = value + 1 WHERE key = ?", (key,))
    return conn.execute("SELECT value FROM counters WHERE key = ?", (key,)).fetchone()[0]


def seed_counter(conn: sqlite3.Connection, key: str, last_used: int) -> None:
    """Start a counter after `last_used`. Does nothing if the counter already exists."""
    _require_transaction(conn)
    conn.execute(
        "INSERT INTO counters (key, value) VALUES (?, ?) ON CONFLICT (key) DO NOTHING",
        (key, last_used),
    )


def format_project_number(n: int) -> str:
    if not 1 <= n <= 9999:
        raise ValueError(f"project number out of range: {n}")
    return f"{n:04d}"


def format_document_number(year: int, n: int) -> str:
    if not 1 <= n <= 999:
        raise ValueError(f"document number {n} for {year} does not fit in three digits")
    return f"{year % 100:02d}{n:03d}"


def format_report_number(project_number: str, n: int) -> str:
    return f"{project_number}-R{n:02d}"


def allocate_project_number(conn: sqlite3.Connection) -> str:
    return format_project_number(next_value(conn, PROJECT_COUNTER))


def allocate_document_number(conn: sqlite3.Connection, year: int) -> str:
    """The next quote or invoice number for the calendar year of the issue date."""
    return format_document_number(year, next_value(conn, f"document:{year}"))


def allocate_report_number(conn: sqlite3.Connection, project_number: str) -> str:
    return format_report_number(project_number, next_value(conn, f"report:{project_number}"))
