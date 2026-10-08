// Invoice or tax invoice: one page, no cover. Data contract: see examples/render_examples.py.
#import "base.typ": *

#let data = load-data()
#let inv = data.invoice
#let b = data.business
#show: setup.with(data, running-header: false)

#grid(
  columns: (1fr, auto),
  align: (left + top, right + top),
  logo(width: 50mm),
  [
    #text(size: 22pt, weight: "bold", fill: colours.deep, upper(data.doc.title)) \
    #text(size: 12pt, data.doc.reference)
  ],
)
#v(4mm)
#line(length: 100%, stroke: 1pt + colours.accent)
#v(4mm)

#grid(
  columns: (1fr, 1fr, auto),
  column-gutter: 8mm,
  party("Bill to", data.client.name, (
    ..(if data.contact != none { ("Attn: " + data.contact.name,) } else { () }),
    ..data.client.address,
    ..(if data.client.abn != "" { (b.abn_label + " " + data.client.abn,) } else { () }),
  )),
  party("From", b.display_name, (b.abn_label + " " + b.abn, b.email)),
  grid(
    columns: 2,
    column-gutter: 4mm,
    row-gutter: 2mm,
    label-text("Issued"), data.doc.date,
    label-text("Due"), strong(inv.due_date),
    label-text("Project"), data.project.number,
    label-text("Quote"), inv.quote_reference,
  ),
)

#v(10mm)
#table(
  columns: (1fr, auto),
  align: (left, right),
  stroke: (x, y) => if y == 0 { (bottom: 0.75pt + colours.deep) },
  table.header(label-text("Description"), label-text("Amount")),
  [#strong(data.project.title) \ #inv.description], inv.subtotal,
)
#let gst = data.business.gst_registered
#align(right, table(
  columns: (auto, 30mm),
  align: (left, right),
  stroke: none,
  ..if gst {
    (
      [Subtotal], inv.subtotal,
      inv.tax_label, inv.tax,
      table.hline(stroke: 0.75pt + colours.deep),
    )
  },
  strong[Total due (#data.currency)], strong(inv.total),
))
#if not gst {
  align(right, text(size: 9pt, fill: colours.muted)[
    No #inv.tax_name is charged: #data.business.display_name is not registered for #inv.tax_name.
  ])
}

#v(1fr)
#block(fill: colours.deep.lighten(92%), inset: 5mm, width: 100%, radius: 2pt)[
  #label-text("Payment") \
  Please pay by #strong(inv.due_date) (#inv.payment_terms_days days) by bank transfer, quoting
  #strong(data.doc.reference). \
  #v(1mm)
  #grid(
    columns: 2,
    column-gutter: 6mm,
    row-gutter: 1.5mm,
    label-text("Account name"), data.bank.account_name,
    label-text("BSB"), data.bank.bsb,
    label-text("Account"), data.bank.account_number,
  )
]
