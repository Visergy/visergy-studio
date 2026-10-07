# Design

## 1. Purpose and scope

A tiny Python CLI (uv, no front end) that produces proposals (quotes), invoices and reports for Visergy, a Melbourne sole-trader consulting business. Typst templates render the PDFs in a shared brand style. One central SQLite database holds everything else.

A "proposal" is the PDF rendered from a quote record: the database, numbering and CLI keep the name `quote`, the document title says "Proposal". Reports are written in Markdown in the project folder and rendered with project and client details taken from the database.

Out of scope: email, credit notes, payment tracking beyond a paid date, a front end.

## 2. Where things live

- **Project folders** sync to Nextcloud. Each has a visible control file, `project.txt`, containing only the project number (for example `0059`). New project folders are named like the old ones: `0059-PhilipStreet`. The CLI finds it by walking up from the current folder.
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
| `projects` | number (`0059`), client_id, title, status |
| `project_contacts` | project_id, contact_id, role |
| `quotes` | project_id, number (`26001`, null until issued; shared sequence with invoices), version, status, body_json, fee_cents (ex-GST), tax_rate_bp, tax_cents, total_cents, validity_days, issue_date, terms_version, terms_hash, payment_terms_days, render_json, pdf_path, pdf_sha256 |
| `invoices` | project_id, quote_id, number (`26002`, null until issued; shared sequence with quotes), status, description, subtotal_cents, tax_rate_bp, tax_cents, total_cents, is_tax_invoice, issue_date, due_date, payment_terms_days, paid_date, render_json, pdf_path, pdf_sha256 |
| `reports` | project_id, number (`0059-R01`, null until first issued), revision (`A`, `B`, ...), status, title, source_path, source_sha256, issue_date, render_json, pdf_path, pdf_sha256 |
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
- Accepting an expired quote warns but is allowed.
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
- A report can only be issued for a project with an accepted quote.
- Numbers are per project (`0059-R01`, counter key `report:0059`), allocated at the first issue. Revisions are letters (`A`, `B`, ...). A new revision is a new row with the same number, like quote versions.
- At issue the row freezes: the source path, a sha256 over the Markdown and every referenced image, the render JSON, the PDF path and its sha256.
- The document control table in the PDF lists the issued revisions of that report number (revision, date, title) from the database.

### Numbering

Visergy traded from 2014 to 2018 (projects `0001` to `0058`, invoices `14004` to `14071`) and is restarting. The old records are not imported: they are not needed as a record (tax years long closed), and the old folders and the Saasu export in Nextcloud remain as the archive. The tool only continues the conventions, so new work looks continuous with the old.

- **Projects**: four digits, one sequence that never resets. The counter is seeded once from `config.toml` (`numbering.last_project = 58`) so the first new project is `0059`. The `9001`-`9004` house projects were a separate series and are left alone.
- **Quotes and invoices** share one sequence per calendar year: two-digit year plus a three-digit count, `26001`, `26002`, ... then `27001` from 1 January 2027. The old scheme was meant this way (it began `2014/01`, then `14004`) but never rolled over, so every old number is `14xxx` and none can collide. Quotes took numbers from the same sequence in the old scheme too, so invoice numbers have gaps; uniqueness is all the ATO needs. A quote revision keeps its number with a version: `26001 v2`.
- **Reports**: per project, `0059-R01`, with lettered revisions.
- **PDF names** follow the old files: `Proposal_26001-v1.pdf`, `Invoice_26002.pdf`, `Report_0059-R01-B.pdf`.

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
5. `config.py` (**done**, pulled forward 2026-10-08), then `invoicing.py` (cap rule, remainder) and `queries.py` (derived statuses) with tests.
6. Render-data builders: turn database rows plus config and locale into the template JSON (replacing the sample builders in `examples/render_examples.py`).
7. CLI: `init` (creates the database and seeds the project counter from `numbering.last_project`), `backup`, `client`, `project`.
8. Quote commands, then invoice commands, then report commands (`report-starter.md`, source hash at issue).
9. `vis status`, `vis restore`, polish.

## 11. Decisions

Adopted from your original design: everything in sections 1 to 5 not marked below, plus the CLI-only approach, Typst, one SQLite database, control-file discovery, the non-synced live database with dated snapshots, and gitignored secrets.

Proposed defaults (answers to your open questions plus additions). Change any of them freely:

- Quote text format is TOML, stored as JSON in the database.
- Numbering continues the conventions Visergy used in 2014-2018 (see "Numbering" in section 5).
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
- Contents page and numbered headings and figures are on by default. No confidentiality notice; the cover carries a copyright line instead (see the cover revision below).
- Rendering was built before the database so example output could be reviewed early. The template JSON contract is defined by the builders in `examples/render_examples.py` until step 6 moves them into the package.
- Report images: inline Markdown image tags only, relative paths inside the report folder (symlinks that escape it are rejected), no remote URLs. Images are copied to `/report/` in the build folder.
- Page numbers count every page, including the cover and back page.
- Brand: logos and the sunburst are SVGs converted from the original EPS files; the cover has a blue field down to a shallow diagonal (earlier versions added a translucent turquoise band, then a parallel blue stripe; both were dropped, see the cover revision below), a small white sunburst top right, the title on blue, details on white below and a contact strip at the foot; the back page is the cover turned through 180 degrees (white above with the business details, blue below the diagonal with the white logo, sunburst bottom left, thin strip at the top) so the two balance as a pair. Myriad Pro is commercially licensed, so Source Sans 3 (OFL) is bundled in its place. See `brand/README.md`.

Cover revision (2026-10-08), from an outside design review, applied to proposals and reports:

- The sunburst is the one graphic device. The blue field ends at a single diagonal; the white gap and second stripe are gone (they read as a generic template).
- Everything sits on the 22mm cover margins. The details table spans the full width between them, under a thin turquoise rule, so its edges line up with the title and the strip text.
- The title is measured: 40pt if it fits on one line or two, else 32pt, else 26pt wrapping freely. Two-line titles are balanced so no word sits alone on a line. The title block is anchored to the foot of the blue field, with the subtitle in a heavier weight, more contrast and a clear gap.
- Report details drop the duplicated revision: "Document 0059-R01" and "Revision B · <description of that revision>". Proposals and reports show the contact as "Attention".
- The cover strip carries only the email (left) and a copyright line, "© <issue year> Visergy. All rights reserved." (right); the text is built in Python (`doc.copyright`). No phone or ABN on the cover: the ABN goes on the back page only.
- Your address and phone appear on no document. Back pages show the name, ABN and email (`back-page(data, contact: true)` brings the address and phone back), and the invoice "From" block shows the name, ABN and email.
- Dates drop the leading zero ("7 October 2026"): `locale.toml` uses `%-d`, which `render.format_date` supports on every platform.
- Labels are semibold and the muted colour is darker (`#595959`); the contact strip text is 10pt.
- The back page shows "Visergy" and the ABN without "trading as".

Settled 2026-10-08:

- No Docker. It is a single-user CLI with the live database on local disk and backups going to Nextcloud, so a container adds nothing. This is a deliberate exception to the general preference to containerise.
- Accepting an expired quote prints a warning and goes ahead. It is not blocked.
- A report cannot be issued unless its project has an accepted quote. Enforce this in the database (a trigger on issue) and give a clear CLI error.
- Restore is a `vis restore` command (build order step 9). It lists or takes a named snapshot, runs an integrity check and a schema version check, refuses to replace a live database without `--force` (and then renames the old file rather than deleting it), copies with the backup API, migrates, and scans project folders for issued PDFs numbered beyond the counters so a restored older snapshot cannot reuse a number.

Config (2026-10-08):

- `config.py` loads `config.toml` from `VISERGY_CONFIG`, else the repo root; `VISERGY_DB` overrides `[paths].database`. It checks types, the ABN checksum and the BSB format, and normalises both (`12 345 678 901`, `123-456`).
- Fields still holding the `config.example.toml` values load without error so the tool works while details are filled in. `Config.placeholders()` lists them; issuing a document must refuse while a field it prints is still a placeholder (to wire in at step 8).
- Bank fields are kept out of reprs, and config errors name the field, never its value.
- Not registered for GST: proposals show the fixed fee alone and invoices show the total alone, each with a "No GST is charged" note, rather than a 0% GST row. The invoice title is "Invoice".
- `examples/render_examples.py` uses the business and bank details from `config.toml` when it exists; the render tests always use `examples/sample.toml`.

Still open:

- Exact wording of the standard terms (the v1 file is a starting draft).
