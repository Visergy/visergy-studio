from datetime import date

import pytest

from visergy.errors import InvalidTransition
from visergy.states import (
    INVOICE_TRANSITIONS,
    QUOTE_TRANSITIONS,
    can_revise_quote,
    check_invoice_transition,
    check_quote_transition,
    is_expired,
    quote_display_status,
    valid_until,
)


def _all_pairs(table):
    return [(old, new) for old in table for new in table]


@pytest.mark.parametrize("old, new", _all_pairs(QUOTE_TRANSITIONS))
def test_quote_transitions(old, new):
    allowed = {("draft", "issued"), ("issued", "accepted"), ("issued", "declined")}
    if (old, new) in allowed:
        check_quote_transition(old, new)
    else:
        with pytest.raises(InvalidTransition):
            check_quote_transition(old, new)


@pytest.mark.parametrize("old, new", _all_pairs(INVOICE_TRANSITIONS))
def test_invoice_transitions(old, new):
    allowed = {("draft", "issued"), ("issued", "paid"), ("issued", "void")}
    if (old, new) in allowed:
        check_invoice_transition(old, new)
    else:
        with pytest.raises(InvalidTransition):
            check_invoice_transition(old, new)


def test_unknown_status_rejected():
    with pytest.raises(InvalidTransition):
        check_quote_transition("expired", "accepted")
    with pytest.raises(InvalidTransition):
        check_invoice_transition("issued", "unpaid")


@pytest.mark.parametrize(
    "status, ok",
    [("draft", False), ("issued", True), ("declined", True), ("accepted", False)],
)
def test_can_revise_quote(status, ok):
    assert can_revise_quote(status) is ok


def test_valid_until():
    assert valid_until(date(2026, 10, 1), 30) == date(2026, 10, 31)


def test_expiry_boundary():
    issued = date(2026, 10, 1)
    assert not is_expired("issued", issued, 30, date(2026, 10, 31))  # last valid day
    assert is_expired("issued", issued, 30, date(2026, 11, 1))


@pytest.mark.parametrize("status", ["draft", "accepted", "declined"])
def test_only_issued_quotes_expire(status):
    assert not is_expired(status, date(2020, 1, 1), 30, date(2026, 1, 1))


def test_expired_needs_issue_date():
    assert not is_expired("issued", None, 30, date(2026, 1, 1))


def test_display_status():
    issued = date(2026, 10, 1)
    assert quote_display_status("issued", issued, 30, date(2026, 10, 5)) == "issued"
    assert quote_display_status("issued", issued, 30, date(2026, 12, 1)) == "expired"
    assert quote_display_status("accepted", issued, 30, date(2026, 12, 1)) == "accepted"
