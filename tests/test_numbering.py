import pytest

from visergy.numbering import (
    PROJECT_COUNTER,
    allocate_document_number,
    allocate_project_number,
    allocate_report_number,
    format_document_number,
    format_project_number,
    format_report_number,
    next_value,
    seed_counter,
)


def test_formats():
    assert format_project_number(59) == "0059"
    assert format_project_number(1234) == "1234"
    assert format_document_number(2026, 1) == "26001"
    assert format_document_number(2026, 999) == "26999"
    assert format_document_number(2105, 7) == "05007"
    assert format_report_number("0059", 1) == "0059-R01"


@pytest.mark.parametrize("n", [0, 10000])
def test_project_number_range(n):
    with pytest.raises(ValueError):
        format_project_number(n)


@pytest.mark.parametrize("n", [0, 1000])
def test_document_number_range(n):
    with pytest.raises(ValueError):
        format_document_number(2026, n)


def test_refuses_outside_transaction(conn):
    with pytest.raises(RuntimeError):
        next_value(conn, PROJECT_COUNTER)
    with pytest.raises(RuntimeError):
        seed_counter(conn, PROJECT_COUNTER, 58)


def test_projects_continue_after_seed(conn):
    conn.execute("BEGIN IMMEDIATE")
    seed_counter(conn, PROJECT_COUNTER, 58)
    assert allocate_project_number(conn) == "0059"
    assert allocate_project_number(conn) == "0060"
    conn.execute("COMMIT")


def test_seed_never_resets_a_counter(conn):
    conn.execute("BEGIN IMMEDIATE")
    seed_counter(conn, PROJECT_COUNTER, 58)
    assert allocate_project_number(conn) == "0059"
    seed_counter(conn, PROJECT_COUNTER, 58)
    assert allocate_project_number(conn) == "0060"
    conn.execute("COMMIT")


def test_unseeded_projects_start_at_one(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_project_number(conn) == "0001"
    conn.execute("COMMIT")


def test_documents_share_one_sequence_per_year(conn):
    conn.execute("BEGIN IMMEDIATE")
    quote = allocate_document_number(conn, 2026)
    invoice = allocate_document_number(conn, 2026)
    assert (quote, invoice) == ("26001", "26002")
    assert allocate_document_number(conn, 2027) == "27001"
    assert allocate_document_number(conn, 2026) == "26003"
    conn.execute("COMMIT")


def test_document_numbers_continue_across_transactions(conn):
    for expected in ("26001", "26002"):
        conn.execute("BEGIN IMMEDIATE")
        assert allocate_document_number(conn, 2026) == expected
        conn.execute("COMMIT")


def test_rollback_burns_no_number(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_document_number(conn, 2026) == "26001"
    conn.execute("ROLLBACK")
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_document_number(conn, 2026) == "26001"
    conn.execute("COMMIT")


def test_report_numbers_are_per_project(conn):
    conn.execute("BEGIN IMMEDIATE")
    assert allocate_report_number(conn, "0059") == "0059-R01"
    assert allocate_report_number(conn, "0059") == "0059-R02"
    assert allocate_report_number(conn, "0060") == "0060-R01"
    conn.execute("COMMIT")
