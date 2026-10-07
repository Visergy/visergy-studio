"""Legal status transitions, in one place.

Stored quote statuses:   draft -> issued -> accepted | declined
Stored invoice statuses: draft -> issued -> paid | void

Derived, never stored: expired (quote), superseded (quote), unpaid / overdue (invoice),
not-yet-invoiced (quote).
"""

from __future__ import annotations

from datetime import date, timedelta

from .errors import InvalidTransition

QUOTE_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"issued"}),
    "issued": frozenset({"accepted", "declined"}),
    "accepted": frozenset(),
    "declined": frozenset(),
}

INVOICE_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"issued"}),
    "issued": frozenset({"paid", "void"}),
    "paid": frozenset(),  # reversing a paid invoice needs a credit note (out of scope)
    "void": frozenset(),
}


def _check(kind: str, table: dict[str, frozenset[str]], old: str, new: str) -> None:
    if old not in table:
        raise InvalidTransition(f"unknown {kind} status: {old!r}")
    if new not in table:
        raise InvalidTransition(f"unknown {kind} status: {new!r}")
    if new not in table[old]:
        raise InvalidTransition(f"{kind} cannot go from {old} to {new}")


def check_quote_transition(old: str, new: str) -> None:
    _check("quote", QUOTE_TRANSITIONS, old, new)


def check_invoice_transition(old: str, new: str) -> None:
    _check("invoice", INVOICE_TRANSITIONS, old, new)


def can_revise_quote(status: str) -> bool:
    """A new version may be started from an issued or declined quote, never from an accepted one."""
    return status in {"issued", "declined"}


def valid_until(issue_date: date, validity_days: int) -> date:
    return issue_date + timedelta(days=validity_days)


def is_expired(status: str, issue_date: date | None, validity_days: int, today: date) -> bool:
    """Derived: an issued quote is expired once today is past issue date + validity."""
    if status != "issued" or issue_date is None:
        return False
    return today > valid_until(issue_date, validity_days)


def quote_display_status(
    status: str, issue_date: date | None, validity_days: int, today: date
) -> str:
    return "expired" if is_expired(status, issue_date, validity_days, today) else status
