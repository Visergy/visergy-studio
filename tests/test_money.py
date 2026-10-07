from decimal import Decimal

import pytest

from visergy.errors import MoneyError
from visergy.money import (
    calc_tax_cents,
    format_money,
    format_rate_bp,
    from_cents,
    parse_amount,
    rate_to_bp,
    to_cents,
    totals,
)


@pytest.mark.parametrize(
    "text, cents",
    [
        ("0", 0),
        ("99", 9900),
        ("$99", 9900),
        ("$ 99", 9900),
        ("1234.5", 123450),
        ("1,234.50", 123450),
        ("12,345,678.90", 1234567890),
        (".5", 50),
        ("  42.01  ", 4201),
    ],
)
def test_parse_amount_valid(text, cents):
    assert parse_amount(text) == cents


@pytest.mark.parametrize(
    "text",
    ["", "$", ".", ",", "1.", "1,2,3", "1,23", "12,3456", "-5", "1e2", "abc", "1.234", "$-1"],
)
def test_parse_amount_invalid(text):
    with pytest.raises(MoneyError):
        parse_amount(text)


def test_to_cents_accepts_str_and_decimal():
    assert to_cents("4500.00") == 450000
    assert to_cents(Decimal("0.01")) == 1


@pytest.mark.parametrize("value", [1.5, 100, True, None])
def test_to_cents_rejects_non_decimal_types(value):
    with pytest.raises(MoneyError):
        to_cents(value)


@pytest.mark.parametrize("value", ["-5", "1e2", "NaN", "Infinity", "1.005", Decimal("-1")])
def test_to_cents_rejects_bad_values(value):
    with pytest.raises(MoneyError):
        to_cents(value)


def test_from_cents_round_trip():
    assert from_cents(123450) == Decimal("1234.50")


@pytest.mark.parametrize(
    "cents, text",
    [(0, "$0.00"), (5, "$0.05"), (123450, "$1,234.50"), (-2500, "-$25.00")],
)
def test_format_money(cents, text):
    assert format_money(cents) == text


@pytest.mark.parametrize("rate, bp", [("0.10", 1000), ("0", 0), ("0.075", 750), ("1", 10000)])
def test_rate_to_bp(rate, bp):
    assert rate_to_bp(rate) == bp


@pytest.mark.parametrize("rate", ["0.00001", "-0.1", "x", 0.1])
def test_rate_to_bp_invalid(rate):
    with pytest.raises(MoneyError):
        rate_to_bp(rate)


@pytest.mark.parametrize("bp, text", [(1000, "10%"), (750, "7.5%"), (0, "0%"), (10000, "100%")])
def test_format_rate_bp(bp, text):
    assert format_rate_bp(bp) == text


@pytest.mark.parametrize(
    "subtotal, bp, tax",
    [
        (450000, 1000, 45000),
        (5, 1000, 1),  # 0.5c rounds half up
        (4, 1000, 0),  # 0.4c rounds down
        (15, 1000, 2),  # 1.5c rounds half up, not to even
        (25, 1000, 3),  # 2.5c rounds half up, not to even
        (999, 0, 0),
    ],
)
def test_calc_tax_rounds_half_up(subtotal, bp, tax):
    assert calc_tax_cents(subtotal, bp) == tax


def test_totals_adds_up():
    t = totals(123455, 1000)
    assert t == (123455, 12346, 135801)
    assert t.total_cents == t.subtotal_cents + t.tax_cents
