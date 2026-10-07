"""Money rules.

* Amounts are stored as integer cents. Decimal is used only at the boundary (parsing, rates).
* Floats are rejected everywhere.
* Tax = round_half_up(subtotal x rate), computed once per document.
* Rates are stored as integer basis points (1000 = 10%).
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import NamedTuple

from .errors import MoneyError

# Optional $, then digits with correctly grouped thousands commas (or none), optional decimals.
_AMOUNT_RE = re.compile(r"^\$?\s*(\d{1,3}(,\d{3})+|\d+)?(\.\d+)?$")
_PLAIN_DECIMAL_RE = re.compile(r"^(\d+(\.\d+)?|\.\d+)$")


class Totals(NamedTuple):
    subtotal_cents: int
    tax_cents: int
    total_cents: int


def to_cents(amount: Decimal | str) -> int:
    """Exact, non-negative conversion to cents.

    Rejects floats, ints, NaN, negatives, exponent notation and more than 2 decimal places.
    """
    if isinstance(amount, bool) or not isinstance(amount, (Decimal, str)):
        raise MoneyError(f"amount must be Decimal or str, got {type(amount).__name__}")
    if isinstance(amount, str) and not _PLAIN_DECIMAL_RE.match(amount.strip()):
        raise MoneyError(f"not a valid amount: {amount!r}")
    try:
        d = Decimal(amount)
    except InvalidOperation:
        raise MoneyError(f"not a valid amount: {amount!r}") from None
    if not d.is_finite() or d < 0:
        raise MoneyError(f"not a valid amount: {amount!r}")
    cents = d * 100
    if cents != cents.to_integral_value():
        raise MoneyError(f"amount has more than 2 decimal places: {amount!r}")
    return int(cents)


def parse_amount(text: str) -> int:
    """Parse user input like '1,234.50' or '$99' into cents. Non-negative only."""
    cleaned = text.strip()
    if not _AMOUNT_RE.match(cleaned):
        raise MoneyError(f"not a valid amount: {text!r}")
    return to_cents(cleaned.lstrip("$").replace(",", "").strip())


def from_cents(cents: int) -> Decimal:
    return Decimal(cents) / 100


def format_money(cents: int, symbol: str = "$") -> str:
    sign = "-" if cents < 0 else ""
    dollars, rem = divmod(abs(cents), 100)
    return f"{sign}{symbol}{dollars:,}.{rem:02d}"


def rate_to_bp(rate: Decimal | str) -> int:
    """'0.10' -> 1000. Rejects rates finer than 0.01%."""
    if isinstance(rate, bool) or not isinstance(rate, (Decimal, str)):
        raise MoneyError(f"rate must be Decimal or str, got {type(rate).__name__}")
    try:
        bp = Decimal(rate) * 10_000
    except InvalidOperation:
        raise MoneyError(f"not a valid rate: {rate!r}") from None
    if not bp.is_finite() or bp != bp.to_integral_value() or bp < 0:
        raise MoneyError(f"not a valid rate: {rate!r}")
    return int(bp)


def format_rate_bp(rate_bp: int) -> str:
    """1000 -> '10%', 750 -> '7.5%'."""
    return f"{(Decimal(rate_bp) / 100).normalize():f}%"


def calc_tax_cents(subtotal_cents: int, rate_bp: int) -> int:
    exact = Decimal(subtotal_cents) * Decimal(rate_bp) / Decimal(10_000)
    return int(exact.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def totals(subtotal_cents: int, rate_bp: int) -> Totals:
    tax = calc_tax_cents(subtotal_cents, rate_bp)
    return Totals(subtotal_cents, tax, subtotal_cents + tax)
