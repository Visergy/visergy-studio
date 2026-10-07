# Design

## 1. Purpose and scope

A tiny Python CLI (uv, no front end) that produces proposals (quotes), invoices and reports for Visergy, a Melbourne sole-trader consulting business. Typst templates render the PDFs in a shared brand style. One central SQLite database holds everything else.

A "proposal" is the PDF rendered from a quote record: the database, numbering and CLI keep the name `quote`, the document title says "Proposal". Reports are written in Markdown in the project folder and rendered with project and client details taken from the database.

Out of scope: email, credit notes, payment tracking beyond a paid date, a front end.

## 2. Where things live

- **Project folders** sync to Nextcloud. Each has a visible control file, `project.txt`, containing only the project number (for example `P2026-001`). The CLI finds it by walking up from the current folder.
- **Live database**: one fixed local path, on one machine, never inside a synced folder. The path comes from `config.toml` or the `VISERGY_DB` environment variable. If the file is missing the CLI fails with a clear message instead of creating an empty one.
- **Snapshots**: after every change, a dated copy of the database is written to the synced backup folder using SQLite's backup API. Keep the newest N plus the newest per UTC day.
- **Brand assets** (`brand/`, committed): logo, `theme.toml` (colours, fonts, page setup) and bundled fonts. **Templates** live in `templates/`.
- **Report sources** live in the project folder: a Markdown file plus its images (for example `report.md` and `figures/`).
- **Git** holds code, templates, brand assets, terms, locale and docs only. The database, PDFs, `config.toml` and bank details are gitignored.
- **PDFs** are saved in the project folder. The database stores a path relative to that folder. Draft PDFs go to a temp or cache folder so a project folder only ever contains issued documents.

## 3. Data model

Every table has an internal integer `id`. Documents also have a unique human number.

| Table | Key columns |
|---|---|
| `clients` | name, abn, address, notes |
| `contacts` | client_id, name, email, phone, role |
| `projects` | number (`P2026-001`), client_id, title, status |
| `project_contacts` | project_id, contact_id, role |
| `quotes` | project_id, number (`Q-0001`, null until issued), version, status, body_json, fee_cents (ex-GST), tax_rate_bp, tax_cents, total_cents, validity_days, issue_date, terms_version, terms_hash, payment_terms_days, render_json, pdf_path, pdf_sha256 |
| `invoices` | project_id, quote_id, number (`INV-0001`, null until issued), status, description, subtotal_cents, tax_rate_bp, tax_cents, total_cents, is_tax_invoice, issue_date, due_date, payment_terms_days, paid_date, render_json, pdf_path, pdf_sha256 |
| `reports` | project_id, number (`P2026-001-R01`, null until first issued), revision (`A`, `B`, ...), status, title, source_path, source_sha256, issue_date, render_json, pdf_path, pdf_sha256 |
| `counters` | key, value (number allocation) |
| `events` | ts, entity_type, entity_id, action, detail (append-only audit trail) |

Constraints to put in the schema:

- `UNIQUE(number, version)` on quotes, `UNIQUE(number)` on invoices, `UNIQUE(number, revision)` on reports.
- A partial unique index allowing at most one `accepted` quote version per quote number.
- `CHECK` on status values, `total = subtotal + tax`, and "non-draft rows must have a number, issue date and render_json".
- Triggers that reject changes to issued rows (everything except status, paid date and void fields) and reject deleting issued rows. Events are append-only.
- A trigger so a version cannot be accepted once a higher version has been issued.
- Invoice and its quote must belong to the same project.
- Use `PRAGMA user_version` and numbered migration files from the start.

## 4. Money and tax

- Dollar amounts to 2 decimal places, stored as integer cents, Decimal arithmetic at the boundary.
- Tax is always tracked (`tax_rate_bp`, `tax_cents`, `total_cents`) even at 0%.
- The rate is recorded when the document is issued, along with whether it went out as a "Tax invoice".
- Rounding: `tax = round_half_up(subtotal x rate)`, once per document.
- The quote fee is ex-GST. The over-invoicing check compares ex-tax subtotals so rounding cannot drift across progress invoices.
- If `gst_registered` is false: tax rate is 0 and the "Tax invoice" title is hard-blocked.

## 5. Quotes and invoices

- Quotes are always a single fixed fee.
- Quote statuses stored: draft, issued, accepted, declined. **Expired** and **superseded** are derived (issue date plus validity days; a higher issued version exists).
- Changing an issued quote creates a new version row with the same number. Revising an accepted quote is not allowed.
- Invoice statuses: draft, issued, paid, void. Changing an issued invoice means void and reissue. A paid invoice cannot be voided (that needs a credit note, out of scope).
- Invoices point at the specific accepted quote version row. Several invoices may reference one quote (progress payments).
- The tool refuses an invoice that would take the issued-plus-paid subtotal over the quote fee, unless overridden. The override is recorded on the invoice. Void invoices drop out of the total and free that budget.
- A "final invoice = remainder" helper computes what is left.
- "Not yet invoiced" and "invoiced but unpaid" are queries.

### Reports

- A report is a Markdown file in the project folder, with a TOML front matter block between `+++` lines (title, subtitle, optional `toc = false`). Images use normal Markdown tags with paths relative to the Markdown file; the alt text becomes the figure caption.
- Project number and title, client name and address and the project contact come from the database (found via `project.txt`), never from the Markdown.
- Report statuses stored: draft, issued. **Superseded** is derived (a later revision is issued).
- Numbers are per project (`P2026-001-R01`, counter key `report:P2026-001`), allocated at the first issue. Revisions are letters (`A`, `B`, ...). A new revision is a new row with the same number, like quote versions.
- At issue the row freezes: the source path, a sha256 over the Markdown and every referenced image, the render JSON, the PDF path and its sha256.
- The document control table in the PDF lists the issued revisions of that report number (revision, date, title) from the database.

## 6. Issue procedure (one transaction)

1. Check the transition is legal and, for invoices, the over-invoicing rule.
2. Allocate the number from `counters` (for a report revision after the first, reuse the number and take the next revision letter).
3. Build the render JSON snapshot: client name and address, contact, business ABN and bank details, tax rate, terms version and hash, payment terms days, display strings. For reports: the Markdown body, front matter and revision history instead of the money fields.
4. Render the PDF into the project folder and compute its sha256.
5. Update the row (status, number, dates, render_json, pdf_path, pdf_sha256) and write an event.
6. Commit, then write a database snapshot to the backup folder.

If any step fails, roll back (no number burned) and remove any PDF written.

## 7. Rendering

- Typst is pinned (`typst==0.15.0`); fonts are bundled in `brand/fonts/` and system fonts are ignored, so output is the same on every machine.
- Python builds a JSON document from the frozen snapshot and passes it as `sys_inputs={"data": "<json>"}`. Templates read it with `json(bytes(sys.inputs.at("data")))`. This avoids markup injection from characters like `#` or `$` in client text. Checked against typst-py 0.15.0, now pinned.
- Money and dates are formatted in Python and passed as display strings, so templates stay dumb.
- Previews render a DRAFT PDF (watermarked, no number) to a temp folder.
- Brand: templates read `brand/theme.toml` directly with Typst's `toml()` (colours, fonts, logo, page setup). It is our own committed file, not client data, so rule 4 is unaffected.
- Templates: `base.typ` (page setup, header and footer, cover page, back page), `proposal.typ` (cover, body, fee, terms, back page), `invoice.typ` (single page, no cover), `report.typ` (cover, document control, contents, body, back page), plus `report-starter.md` for `vis report new`.
- Markdown is rendered inside Typst by the `cmarker` package (pinned, `@preview/cmarker:0.1.10`), which takes the Markdown as a string from the JSON. It must always be called with `raw-typst: false`: by default an HTML comment `<!--raw-typst ...-->` in the Markdown runs as Typst code (confirmed in a spike).
- Build folder: Typst can only read files under one root. Python copies `templates/`, `brand/`, and for reports the referenced images, into a temp build folder and compiles there with `root` set to it. Python checks every image reference exists first, and rejects paths that escape the report folder.
- Typst downloads `cmarker` from Typst Universe on first use and caches it. If offline or reproducibility becomes a problem, vendor it into the repo.

## 8. Config and locale

- `config.toml` (gitignored): business identity, ABN, bank details, GST-registered flag, paths, defaults, backup retention.
- `locale.toml` (committed): AUD, GST 10%, "Tax invoice" and "Invoice" titles, ABN label, date format, financial year start 1 July, 14-day payment terms.
- Standard terms live in `terms/terms-v<N>.toml`. Each quote stores the terms version and a hash of the content at issue. Payment terms days is snapshotted onto each document.

Tax invoice content (ABN, the words "Tax invoice", GST amount, buyer details above the threshold) should be checked against current ATO requirements or with your accountant, and the invoice template should enforce it.

## 9. CLI surface

```
vis init                       create/upgrade the database, take a first snapshot
vis backup
vis client new | list
vis project new | show
vis quote new | preview | issue | revise | accept | decline
vis invoice new | preview | issue | paid | void
vis report new | preview | issue | revise
vis status                     not yet invoiced, invoiced but unpaid
```

`vis quote new --from quote.toml` imports a quote body (see `examples/quote.toml`) into the database as a draft.

`vis report new` copies `templates/report-starter.md` into the current project folder and records a draft. `preview` and `issue` read the Markdown at that moment.

## 10. Build order

1. Tests for the drafted modules; fix what fails. **Done.**
2. Example output (pulled forward, done): `base.typ`, `proposal.typ`, `invoice.typ`, `report.typ`, `render.py`, `reports.py`, render tests, and `examples/render_examples.py`, which renders all three documents from sample data without a database.
3. Schema migration 001 (tables, checks, triggers) and `db.py` (connect, transaction, migrate); tests for triggers and constraints.
4. `backup.py` (backup API, naming, pruning) with tests.
5. `config.py`, then `invoicing.py` (cap rule, remainder) and `queries.py` (derived statuses) with tests.
6. Render-data builders: turn database rows plus config and locale into the template JSON (replacing the sample builders in `examples/render_examples.py`).
7. CLI: `init`, `backup`, `client`, `project`.
8. Quote commands, then invoice commands, then report commands (`report-starter.md`, source hash at issue).
9. `vis status`, polish, restore instructions.

## 11. Decisions

Adopted from your original design: everything in sections 1 to 5 not marked below, plus the CLI-only approach, Typst, one SQLite database, control-file discovery, the non-synced live database with dated snapshots, and gitignored secrets.

Proposed defaults (answers to your open questions plus additions). Change any of them freely:

- Quote text format is TOML, stored as JSON in the database.
- Numbering is continuous and never resets for quotes and invoices; project numbers reset each year.
- One machine uses the database.
- Standard terms are versioned files in git, with the version and a content hash stored on each quote.
- Render data is snapshotted at issue so later config or client edits cannot change a frozen document.
- Integer cents storage; half-up rounding once per document; quote fee ex-GST.
- Quote versions are separate rows; invoices point at the accepted version row.
- Expired and superseded are derived, not stored (this differs from your original status list).
- Triggers enforce frozen rows; `counters`, `events` and basis-point rates are additions to your table list.
- Draft PDFs go to a temp folder, not the project folder.

Reports and branding (added 2026-10-07):

- "Proposal" is the rendered quote, not a new record type. Proposals and reports get the cover and back page; invoices do not.
- Reports are written in Markdown and rendered with `cmarker` inside Typst, not converted with Pandoc: no extra dependency, and the text stays data rather than Typst source.
- Front matter is TOML (`+++`), because `tomllib` is in the standard library and YAML is not.
- Reports are stored in the database with per-project numbers and lettered revisions, so issued revisions are frozen and the document control table can be generated.
- Contents page and numbered headings and figures are on by default. No confidentiality notice for now.
- Rendering was built before the database so example output could be reviewed early. The template JSON contract is defined by the builders in `examples/render_examples.py` until step 6 moves them into the package.
- Report images: inline Markdown image tags only, relative paths inside the report folder (symlinks that escape it are rejected), no remote URLs. Images are copied to `/report/` in the build folder.
- Page numbers count every page, including the cover and back page.
- Brand: logos and the sunburst are SVGs converted from the original EPS files; the cover has a blue field down to a shallow diagonal with a parallel blue stripe below the cut, separated by a narrow white gap (an earlier translucent turquoise band made an off-brand tint, so the cover uses only the card blue and turquoise stays in the logo), a small white sunburst top right, the title on blue, details on white at the lower right and a contact strip at the foot (titles over 45 characters drop from 32pt to 26pt); the back page is the cover turned through 180 degrees (white above with the business details, blue below the band with the white logo, sunburst bottom left, thin strip at the top) so the two balance as a pair. Myriad Pro is commercially licensed, so Source Sans 3 (OFL) is bundled in its place. See `brand/README.md`.

Still open:

- Whether accepting an expired quote should warn or block.
- Exact wording of the standard terms (the v1 file is a starting draft).
- How a restore should work (a `vis restore` command, or documented manual steps).
- Whether a report can be issued for a project with no accepted quote.
