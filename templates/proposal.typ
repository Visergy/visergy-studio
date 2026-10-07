// Proposal: the rendered form of a quote. Data contract: see examples/render_examples.py.
#import "base.typ": *

#let data = load-data()
#let q = data.quote
#show: setup.with(data)

#cover(data, q.title, details: (
  ("Client", data.client.name),
  ("Attention", if data.contact != none { data.contact.name }),
  ("Project", data.project.number + " · " + data.project.title),
  ("Reference", data.doc.reference),
  ("Date", data.doc.date),
  ("Valid until", q.valid_until),
))

#let section(title, items) = if items.len() > 0 {
  heading(level: 1, title)
  list(..items)
}

= Summary
#for para in q.summary.split("\n\n") { par(para.trim()) }

#section("Scope", q.scope)
#section("Deliverables", q.deliverables)
#section("Assumptions", q.assumptions)
#section("Exclusions", q.exclusions)

#if q.timing != "" [
  = Timing
  #q.timing
]

= Fee
#table(
  columns: (1fr, auto),
  align: (left, right),
  stroke: none,
  [Fixed fee (excluding #q.tax_name)], q.fee,
  q.tax_label, q.tax,
  table.hline(stroke: 0.75pt + colours.primary),
  strong[Total], strong(q.total),
)
Invoices are payable within #q.payment_terms_days days. This proposal is valid until #q.valid_until.
To accept it, reply in writing quoting #data.doc.reference.

= Terms
#text(size: 9pt, fill: colours.muted)[Standard terms #data.terms.version]
#for s in data.terms.sections {
  heading(level: 2, s.heading)
  par(s.body)
}

#back-page(data)
