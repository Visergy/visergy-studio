"""Gap-free, never-reused document numbers.

Numbers come from the `counters` table and MUST be allocated inside the same transaction that
issues the document. If that transaction rolls back (for example the PDF fails to render), the
counter rolls back with it, so no number is burned. Voided documents keep their numbers.

Quotes and invoices use one continuous sequence (never reset). Project numbers reset each year.
"""

from __future__ import annotations

import sqlite3


def next_value(conn: sqlite3.Connection, key: str) -> int:
    if not conn.in_transaction:
        raise RuntimeError("allocate numbers inside a transaction (db.transaction)")
    conn.execute(
        "INSERT INTO counters (key, value) VALUES (?, 0) ON CONFLICT (key) DO NOTHING", (key,)
    )
    conn.execute("UPDATE counters SET value = value + 1 WHERE key = ?", (key,))
    return conn.execute("SELECT value FROM counters WHERE key = ?", (key,)).fetchone()[0]


def format_quote_number(n: int) -> str:
    return f"Q-{n:04d}"


def format_invoice_number(n: int) -> str:
    return f"INV-{n:04d}"


def format_project_number(year: int, n: int) -> str:
    return f"P{year}-{n:03d}"


def allocate_quote_number(conn: sqlite3.Connection) -> str:
    return format_quote_number(next_value(conn, "quote"))


def allocate_invoice_number(conn: sqlite3.Connection) -> str:
    return format_invoice_number(next_value(conn, "invoice"))


def allocate_project_number(conn: sqlite3.Connection, year: int) -> str:
    return format_project_number(year, next_value(conn, f"project:{year}"))
