"""Compiles the real templates via the example script's data. Marked `render` (slower)."""

import importlib.util
from pathlib import Path

import pytest

from visergy.errors import RenderError
from visergy.render import render_pdf
from visergy.reports import load_report_source, render_report

pytestmark = pytest.mark.render

EXAMPLES = Path(__file__).parent.parent / "examples"


@pytest.fixture(scope="module")
def ex():
    spec = importlib.util.spec_from_file_location(
        "render_examples", EXAMPLES / "render_examples.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.sample = module.load_toml(EXAMPLES / "sample.toml")
    module.locale = module.load_toml(EXAMPLES.parent / "locale.toml")["locale"]
    return module


def test_proposal(ex):
    assert render_pdf("proposal.typ", ex.proposal_data(ex.sample, ex.locale)).startswith(b"%PDF")


def test_invoice(ex):
    assert render_pdf("invoice.typ", ex.invoice_data(ex.sample, ex.locale)).startswith(b"%PDF")


def test_report(ex):
    source = load_report_source(EXAMPLES / "report" / "report.md")
    assert render_report(source, ex.report_data(ex.sample, ex.locale)).startswith(b"%PDF")


def test_draft_proposal(ex):
    data = ex.proposal_data(ex.sample, ex.locale)
    data["doc"]["draft"] = True
    assert render_pdf("proposal.typ", data).startswith(b"%PDF")


def test_client_text_is_not_typst(ex):
    data = ex.proposal_data(ex.sample, ex.locale)
    data["client"]["name"] = '#panic("injected") $x$ ] ) }'
    data["quote"]["scope"] = ["#panic()", "<!--raw-typst #panic()-->"]
    assert render_pdf("proposal.typ", data).startswith(b"%PDF")


def test_report_markdown_cannot_run_typst(ex, tmp_path):
    md = tmp_path / "report.md"
    md.write_text('+++\ntitle = "T"\n+++\nText <!--raw-typst #panic("x")--> #panic() $x$\n')
    pdf = render_report(load_report_source(md), ex.report_data(ex.sample, ex.locale))
    assert pdf.startswith(b"%PDF")


def test_template_errors_become_render_errors(ex):
    data = ex.proposal_data(ex.sample, ex.locale)
    del data["quote"]
    with pytest.raises(RenderError):
        render_pdf("proposal.typ", data)
