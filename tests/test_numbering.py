import pytest

from visergy.numbering import (
    allocate_invoice_number,
    allocate_project_number,
    allocate_quote_number,
    format_invoice_number,
    format_project_number,
    format_quote_number,
    next_value,
)


def test_formats():
    assert format_quote_number(1) == "Q-0001"
    assert format_invoice_number(12) == "INV-0012"
    assert format_project_number(2026, 3) == "P2026-003"
    assert format_quote_number(12345) == "Q-12345"


def test_refuses_outside_transaction(conn):
    with pytest.raises(RuntimeError):
        next_value(conn, "quote")


def test_numbers_increase(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_quote_number(conn) == "Q-0001"
    assert allocate_quote_number(conn) == "Q-0002"
    conn.execute("COMMIT")
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_quote_number(conn) == "Q-0003"
    conn.execute("COMMIT")


def test_rollback_burns_no_number(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_invoice_number(conn) == "INV-0001"
    conn.execute("ROLLBACK")
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_invoice_number(conn) == "INV-0001"
    conn.execute("COMMIT")


def test_sequences_are_independent(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_quote_number(conn) == "Q-0001"
    assert allocate_invoice_number(conn) == "INV-0001"
    assert allocate_project_number(conn, 2026) == "P2026-001"
    assert allocate_project_number(conn, 2026) == "P2026-002"
    assert allocate_project_number(conn, 2027) == "P2027-001"
    conn.execute("COMMIT")
