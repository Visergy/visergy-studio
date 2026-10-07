# visergy-studio

A small command-line tool (`vis`) that produces proposals, invoices and reports for Visergy, a sole-trader consulting business in Melbourne. It uses Python with uv, one SQLite database, and Typst for the PDFs. Reports are written in Markdown and rendered with a Visergy cover page, back page and project details from the database.

Status: early prototype. The core modules, Typst templates and PDF rendering work and are tested; the database and the CLI are not built yet. The design and build order are in `docs/DESIGN.md`, and the working brief for Claude Code is in `CLAUDE.md`.

## Set up

```
uv sync
cp config.example.toml config.toml     # then edit: ABN, bank details, paths. Never commit it.
```

`config.toml`, the database and PDFs are gitignored. Check `git status` before committing.

## See example output

```
uv run python examples/render_examples.py
```

This renders a proposal, a tax invoice and a report into `examples/output/`, using made-up data from `examples/sample.toml`, `examples/quote.toml` and `examples/report/`. No database or `config.toml` is needed.

## Develop

```
uv run pytest
uv run ruff check . && uv run ruff format .
```

## Layout

- `src/visergy/`: the Python package
- `docs/DESIGN.md`: data model, rules, build order and decisions
- `brand/`: logo, theme colours and fonts used by every template
- `templates/`: Typst templates (`base.typ` shared layout, proposal, invoice, report)
- `terms/`: versioned standard terms (never edit a version once it has been used)
- `locale.toml`: Australian specifics (GST, titles, payment terms)
- `examples/`: sample data and the script that renders example PDFs
