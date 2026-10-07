# Handoff

Where the work stopped, for picking it up on another machine. Last updated 2026-10-08.

## State

- Branch `initial-build` holds all the work so far; `main` still has only the first commit.
  Merge when ready: `git checkout main && git merge initial-build`.
- Build order steps 1 and 2 in `docs/DESIGN.md` are done. Everything else is still to build.
- 169 tests pass; ruff is clean.

What works today:

- Core modules with tests: `money`, `states`, `numbering`, `paths`, `terms`, `render`, `reports`.
- Typst templates for proposals, invoices and reports with the Visergy branding (`templates/`,
  `brand/`).
- `uv run python examples/render_examples.py` renders a sample proposal, invoice and report to
  `examples/output/` from made-up data. No database or `config.toml` is needed.

## Set up on a new machine

```
git clone git@github.com:joncmorgan/visergy-studio.git    # or git fetch, if already cloned
git checkout initial-build
uv sync
uv run pytest
uv run python examples/render_examples.py
```

- The first render downloads the `cmarker` Typst package from Typst Universe, so it needs
  internet once; after that it is cached.
- Fonts are in the repo (`brand/fonts/`), and system fonts are ignored, so PDFs come out the
  same on every machine.
- `config.toml` is not needed yet. When it is, copy `config.example.toml` and fill it in; never
  commit it.

## Decisions made so far

All recorded in `docs/DESIGN.md` section 11. The ones that most shape the next steps:

- **Numbering continues the 2014-2018 conventions** (DESIGN section 5, "Numbering"):
  projects `0059` onwards; quotes and invoices share `YY` + three digits (`26001`, `26002`,
  then `27001` from 1 January 2027); reports `0059-R01`. The old records are not imported. The
  project counter is seeded from `config.toml` `numbering.last_project = 58` by `vis init`.
- **"Proposal" is the rendered quote**, not a separate record.
- **Reports are Markdown** with TOML front matter, rendered by `cmarker` inside Typst, always
  with `raw-typst: false` (otherwise Markdown comments can run Typst code).
- **Brand**: diagonal blue cover with a white-gap blue stripe, back page is the cover turned
  through 180 degrees. Source Sans 3 stands in for Myriad Pro (licensing). Original artwork is in
  Nextcloud `Work/Visergy/Admin/Brand/OneDegree/`; see `brand/README.md`.

## Next step: build order step 3 (schema and `db.py`)

Migration `001` with the tables, CHECK constraints and frozen-row triggers, plus `db.py`
(connect, `BEGIN IMMEDIATE` transactions, `PRAGMA user_version` migrations) and tests for every
trigger and constraint. Points from the review that the schema has to settle:

- A revised quote (`v2`) is a draft that already carries its number, so "number is null until
  issued" only applies to version 1.
- Invoices need void columns (`void_date`, `void_reason`) and a column recording an
  over-invoicing override (`cap_override_reason`).
- Add `created_at` to the main tables.
- Quote and invoice numbers come from one shared counter, so they are unique across both tables
  even though each table only has its own UNIQUE constraint.
- The document number's year comes from the issue date. Issue and due dates use Melbourne
  local time; timestamps stay UTC.
- `numbering.py` expects a `counters(key TEXT PRIMARY KEY, value INTEGER NOT NULL)` table.

## Open questions

- Docker: proposed to skip for this single-user CLI, not yet confirmed.
- Whether accepting an expired quote warns or blocks.
- Whether a report can be issued for a project with no accepted quote.
- How restore works (`vis restore` or documented steps).
- Standard terms wording (`terms/terms-v1.toml` is a draft with TODOs for IP and liability).

## Parked for later

- Cover refinements: the stripe and gap widths, sunburst size (`corner-sunburst`) and text
  positions are near the top of the cover and back-page sections of `templates/base.typ`.
- A Myriad Pro licence that allows PDF embedding would let the real brand font replace
  Source Sans 3 (one line in `brand/theme.toml`).

## A first prompt for Claude Code

> Read CLAUDE.md, HANDOFF.md and docs/DESIGN.md. Start build order step 3: the schema
> migration and db.py, with tests for the triggers and constraints.
