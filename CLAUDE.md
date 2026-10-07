# Visergy admin: brief for Claude Code

A tiny Python CLI (`vis`, managed with uv, no front end) that produces proposals (quotes), invoices and Markdown-authored reports for Visergy, a Melbourne sole-trader consulting business. One central SQLite database, Typst templates for the PDFs, brand assets in `brand/`.

Read `docs/DESIGN.md` first. It holds the data model, the rules and the build order. `HANDOFF.md` says where the last session stopped.

## State of the repo

This is a starter kit, not a working app.

- Present: `pyproject.toml`, `config.example.toml`, `locale.toml`, `terms/terms-v1.toml`, `examples/quote.toml`, `brand/` (logos, theme colours, fonts), core modules in `src/visergy/` (`money`, `states`, `paths`, `numbering`, `terms`, `errors`, `render`, `reports`, `config`) with tests, Typst templates in `templates/` (proposal, invoice, report), and `examples/render_examples.py`, which renders all three from sample data.
- Missing: SQL schema and migrations, `db`, `backup`, `invoicing`, `queries`, the render-data builders and `cli`.
- `numbering.py` assumes a `counters(key, value)` table that the schema must provide.
- `[project.scripts]` is not set yet. Add `vis = "visergy.cli:main"` once `cli.py` exists.

## Commands

```
uv sync
uv run pytest                                # all tests; -m "not render" skips PDF compiles
uv run python examples/render_examples.py    # example PDFs in examples/output/
uv run ruff check . && uv run ruff format .
```

## Rules that must never break

1. Money is integer cents in the database. Decimal only at the boundary. No floats, ever. Tax = round half up of subtotal x rate, computed once per document. Rates are integer basis points (1000 = 10%).
2. Issued documents are frozen. A quote change is a new version row; an invoice change is void and reissue. Enforce this in the database with triggers, not just in Python.
3. Numbers are allocated only at issue, inside the same transaction that issues the document (see `numbering.py`). A rolled-back issue must not burn a number. Voided documents keep their numbers.
4. Data reaches Typst only as a JSON string via `sys.inputs`. Never interpolate client text into Typst source. Report Markdown is rendered with `cmarker` and always with `raw-typst: false`.
5. "Not yet invoiced", "unpaid", "expired" and "superseded" are derived by query. Do not store them.
6. Never commit `config.toml`, the database, PDFs, report sources, or bank details. Do not print bank details in logs, errors or tests.
7. The live database is never in a synced folder. Snapshots use SQLite's backup API (never a file copy) and go to the synced backup folder after every change.
8. Schema changes are new numbered migration files. Never edit a migration that has been applied.

## Conventions

- Python 3.12+, stdlib first. The only runtime dependency is `typst`.
- Expected user-facing failures raise a subclass of `VisergyError`; the CLI prints `error: ...` and exits 1.
- Open SQLite connections with `isolation_level=None` and manage transactions explicitly (`BEGIN IMMEDIATE`).
- Dates are ISO `YYYY-MM-DD` text; timestamps are UTC ISO text.
- Numbering continues Visergy's 2014-2018 conventions (projects `0059`, quotes and invoices `26001`): see "Numbering" in `docs/DESIGN.md`.
- Australian specifics (GST, titles, terms days, financial year) live in `locale.toml`, not in code.

## Working agreement

- Write the tests for a rule before or alongside the code. Priority tests: numbering, the over-invoicing cap, rounding, status transitions, frozen-row triggers.
- Run `uv run pytest` and `uv run ruff check .` before saying a step is done.
- Follow the build order in `docs/DESIGN.md`. One step at a time.
- When you make a design decision, add it to the decisions section of `docs/DESIGN.md`.
- Out of scope: email, credit notes, payment tracking beyond a paid date, a front end.
