"""Render an example proposal, invoice and report to examples/output/.

Uses examples/sample.toml in place of config.toml and the database, so it runs on a fresh checkout:

    uv run python examples/render_examples.py
"""

from __future__ import annotations

import tomllib
from datetime import date, timedelta
from pathlib import Path

from visergy.money import format_money, format_rate_bp, rate_to_bp, to_cents, totals
from visergy.render import render_pdf
from visergy.reports import load_report_source, render_report
from visergy.states import valid_until
from visergy.terms import load_terms

HERE = Path(__file__).parent
REPO = HERE.parent
OUTPUT = HERE / "output"
TODAY = date(2026, 10, 7)


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def fmt_date(d: date, locale: dict) -> str:
    return d.strftime(locale["date_format"])


def common_data(sample: dict, locale: dict, title: str, reference: str) -> dict:
    """The parts every document shares: doc header, business, client, contact, project."""
    b = sample["business"]
    return {
        "doc": {
            "title": title,
            "reference": reference,
            "date": fmt_date(TODAY, locale),
            "draft": False,
        },
        "business": {**b, "display_name": b["trading_as"] or b["name"], "abn_label": "ABN"},
        "client": sample["client"],
        "contact": sample.get("contact"),
        "project": sample["project"],
        "currency": locale["currency"],
    }


def tax_label(locale: dict, rate_bp: int) -> str:
    return f"{locale['tax_name']} ({format_rate_bp(rate_bp)})"


def proposal_data(sample: dict, locale: dict) -> dict:
    body = load_toml(HERE / "quote.toml")
    rate_bp = rate_to_bp(locale["tax_rate"])
    t = totals(to_cents(body["fee"]), rate_bp)
    terms = load_terms("v1", REPO / "terms")
    data = common_data(sample, locale, locale["quote_title"], "Q-0001 v1")
    data["quote"] = {
        "title": body["title"],
        "summary": body["summary"].strip(),
        "scope": body.get("scope", []),
        "deliverables": body.get("deliverables", []),
        "assumptions": body.get("assumptions", []),
        "exclusions": body.get("exclusions", []),
        "timing": body.get("timing", ""),
        "valid_until": fmt_date(valid_until(TODAY, body["validity_days"]), locale),
        "fee": format_money(t.subtotal_cents),
        "tax_name": locale["tax_name"],
        "tax_label": tax_label(locale, rate_bp),
        "tax": format_money(t.tax_cents),
        "total": format_money(t.total_cents),
        "payment_terms_days": locale["payment_terms_days"],
    }
    data["terms"] = {"version": terms.version, "sections": terms.sections}
    return data


def invoice_data(sample: dict, locale: dict) -> dict:
    rate_bp = rate_to_bp(locale["tax_rate"])
    t = totals(to_cents(sample["invoice"]["amount"]), rate_bp)
    days = locale["payment_terms_days"]
    data = common_data(sample, locale, locale["tax_invoice_title"], "INV-0001")
    data["invoice"] = {
        "description": sample["invoice"]["description"],
        "quote_reference": "Q-0001 v1",
        "subtotal": format_money(t.subtotal_cents),
        "tax_label": tax_label(locale, rate_bp),
        "tax": format_money(t.tax_cents),
        "total": format_money(t.total_cents),
        "due_date": fmt_date(TODAY + timedelta(days=days), locale),
        "payment_terms_days": days,
    }
    data["bank"] = sample["bank"]
    return data


def report_data(sample: dict, locale: dict) -> dict:
    data = common_data(sample, locale, locale["report_title"], "P2026-001-R01 Rev B")
    data["report"] = {
        "revision": "B",
        "history": [
            {
                "revision": "A",
                "date": fmt_date(date(2026, 9, 18), locale),
                "description": "Draft for comment",
            },
            {
                "revision": "B",
                "date": fmt_date(TODAY, locale),
                "description": "Issued for information",
            },
        ],
    }
    return data


def main() -> None:
    sample = load_toml(HERE / "sample.toml")
    locale = load_toml(REPO / "locale.toml")["locale"]
    OUTPUT.mkdir(exist_ok=True)

    outputs = {
        "proposal-Q-0001-v1.pdf": render_pdf("proposal.typ", proposal_data(sample, locale)),
        "invoice-INV-0001.pdf": render_pdf("invoice.typ", invoice_data(sample, locale)),
        "report-P2026-001-R01-B.pdf": render_report(
            load_report_source(HERE / "report" / "report.md"), report_data(sample, locale)
        ),
    }
    for name, pdf in outputs.items():
        (OUTPUT / name).write_bytes(pdf)
        print(f"wrote {OUTPUT / name}")


if __name__ == "__main__":
    main()
